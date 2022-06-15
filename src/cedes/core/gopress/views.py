# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 by GoForWeb.be
#
# GNU General Public License (GPL)
#

from cedes.core.gopress.config import ARTICLE_TO_PRINT
from cedes.core.gopress.config import create_xml_file
from cedes.core.gopress.config import FOLDER_TO_PRINT
from cedes.core.gopress.config import GOPRESS_APIKEY
from cedes.core.gopress.config import GOPRESS_BACKUP_PATH
from cedes.core.gopress.config import GOPRESS_DO_BACKUP
from cedes.core.gopress.config import GOPRESS_EMAIL
from cedes.core.gopress.config import GOPRESS_PATH
from cedes.core.gopress.config import GOPRESS_URL
from cedes.core.gopress.config import GOPRESS_XML_FILE_PATH
from cedes.core.gopress.config import PRINT_GOPRESS_REQUEST
from cedes.core.utils import richtextval
from datetime import datetime
from io import BytesIO
from plone.dexterity.utils import createContentInContainer
from plone.namedfile import NamedBlobFile
from Products.Five import BrowserView
from PyPDF2 import PdfFileReader
from PyPDF2 import PdfFileWriter
from PyPDF2 import utils
from xml.etree import ElementTree

import codecs
import httplib2 as http
import json
import logging
import lxml.html
import os
import shutil
import subprocess


try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse

logger = logging.getLogger('CeDES Gopress')

GS_COMMAND = "gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 -dDownsampleColorImages=true " \
    "-dColorImageResolution=260 -dNOPAUSE -dBATCH -sOutputFile=%s " \
    "-c \"<</BeginPage{1.12 1.15 scale -25 -115 translate}>> setpagedevice\" -f %s"


class GoPressView(BrowserView):
    """
      This manage functionnality around GoPress
    """
    def __init__(self, context, request):
        self.context = context
        self.request = request
        create_xml_file()

    def _send_json_request(self, path, extra_headers={}, return_as_raw=False):
        """Send a json request and returns decoded response."""
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json; charset=UTF-8',
            'Cache-Control': 'no-store',
            'Pragma': 'no-cache',
            'expires': 'Mon, 26 Jul 1997 05:00:00 GMT',
            'apikey': GOPRESS_APIKEY,
            'email': GOPRESS_EMAIL,
        }
        headers.update(extra_headers)

        url = GOPRESS_URL
        target = urlparse(url+path)
        method = 'GET'
        body = ''

        h = http.Http()
        logger.info("Executing JSON call '%s'" % path)
        response, content = h.request(
            target.geturl(),
            method,
            body,
            headers)
        if not return_as_raw and content:
            return json.loads(content)
        else:
            return content

    def synchronize(self):
        """Synchronize folders on the FS with Gopress."""
        data = self._send_json_request(path='/user')
        # recreates the metadatas xml file
        root = ElementTree.Element("PB")
        publications = {'tree': ''}
        sync_status = {'errors': [], 'art_count': 0, 'new_art': 0, 'warns': []}

        for json_folder in data['RESPONSE']['RESULTS']:
            # only keep 'user-folders'
            if 'GP:BUNDLE' not in json_folder:
                continue
            # get every usefull informations
            user_folders = json_folder['GP:BUNDLE']
            # if only 1 user-folder, infos is the user-folder directly
            # but if several user-folders, it is a list...  Make a list in any case
            if not isinstance(user_folders, list):
                user_folders = [user_folders, ]
            for user_folder in user_folders:
                infos = user_folder.get('INFO')
                logger.info("Treating folder '%s'" % infos.get('ID'))
                # creates the folder metadata
                folder = ElementTree.SubElement(root, "folder")
                folder_id = infos.get('ID')
                folder.set("id", folder_id)
                ElementTree.SubElement(folder, "folder_name").text = infos.get('TITLE')
                # creates the directory if it does not exists
                folder_path = os.path.join(GOPRESS_PATH, folder_id)
                if not os.path.exists(folder_path):
                    os.mkdir(folder_path)

                # creates the articles metadata
                articles = self.get_articles_xml(folder_id, publications)
                ElementTree.SubElement(folder, "folder_articlecount").text = str(len(articles))
                for article, articleHTML, pdf_path in articles:
                    sync_status['art_count'] += 1
                    folder.append(article)
                    logger.info("Treating article '%s'" % article.get('id'))
                    article_id = article.get('id')
                    # article_publication = article.findtext('article_publication')

                    down_status = self._treat_html_pdf(folder_id, article_id, articleHTML, pdf_path, force=0)
                    if down_status.get('new_art'):
                        sync_status['new_art'] += 1
                    # clean HTML and retrieve metadata : author and abstract
                    # pbmeta = {
                    #    'article_id': article_id,
                    #    'article_title': article.findtext('article_title', ''),
                        # 'article_pubid' : article.findtext('article_pubid', ''),
                        # 'article_publication': article.findtext('article_publication', ''),
                        # 'article_words': article.findtext('article_words', ''),
                        # 'article_page': article.findtext('article_page', ''),
                        # 'article_mode': article.findtext('article_mode', ''),
                        # 'article_date': article.findtext('article_date', ''),
                        # 'article_price': article.findtext('article_price', ''),
                    # }
                    # meta = cleanArticle(folder_id, article_id,
                    #                     article_publication, force=0, pbmeta=pbmeta)
                    # checkMetaForErrors(meta, sync_status,
                    #                    folder_id, user_folder['INFO']['TITLE'],
                    #                    article_id, article.findtext('article_title', ''),
                    #                    article_publication, down_status)

            if GOPRESS_DO_BACKUP:
                self._backup_GP(GOPRESS_XML_FILE_PATH, GOPRESS_BACKUP_PATH, suffix=True)

            base_new = ElementTree.ElementTree(root)
            base_new.write(GOPRESS_XML_FILE_PATH, 'utf-8')

            return sync_status

    def _get_versions_for(self, folder_id):
        """ """
        path = '/versions/{}'.format(folder_id)
        json_versions = self._send_json_request(path=path)
        version_infos = json_versions['RESPONSE']['RESULTS']['GP:BUNDLE']
        # if only one element, we receive a dict, if several we receive a list of dict
        # make sure we always have a list
        if not isinstance(version_infos, list):
            version_infos = [version_infos]
        versions = [version['INFO']['ID'] for version in version_infos]
        return versions

    def _get_articles_for(self, folder_id, version_id, check_for_new=True):
        """ """
        if check_for_new:
            # first do a JSON request without 'article_data' to speed up things
            # if we find new articles, then use 'article_data=true'
            path = '/articles/{}/{}'.format(folder_id, version_id)
        else:
            path = '/articles/{}/{}?articles_data=true'.format(folder_id, version_id)
        json_articles = self._send_json_request(path=path)
        # we receive many things, 'bundle, 'master-bundle', ...
        # what we need is the 'bundle-articles'
        bundle_articles = []
        if not json_articles:
            return bundle_articles
        for bundle in json_articles['RESPONSE']['RESULTS']:
            if bundle['@name'] == 'bundle-articles':
                bundle_articles = bundle.get('GP:ARTICLE') or []
        # one element in 'bundle-articles' is a dict, if several it is a list
        # make sure it is a list in any case
        if not isinstance(bundle_articles, list):
            bundle_articles = [bundle_articles]

        if check_for_new:
            # right, check if we have new articles
            # open current metadatas.xml and check if article id is already there
            xml_to_plone = self.context.restrictedTraverse('@@xml-to-plone')
            for article in bundle_articles:
                article_infos = article['INFO']
                article_id = article_infos.get('ID')
                # if we find an unmanaged article, we need to manage the entire folder
                if not xml_to_plone._get_article_information(folder_id, article_id):
                    return self._get_articles_for(folder_id, version_id, check_for_new=False)
        return bundle_articles

    def _clean_html(self, articleHTML, article_xml):
        """We receive entire HTML, try to remove relevant parts :
           - title;
           - summary;
           - author."""
        if not articleHTML:
            return articleHTML

        tree = lxml.html.fromstring(articleHTML)
        children = tree.getchildren()
        # we will clean first 2 tags
        if not len(children) >= 2:
            return articleHTML

        # remove leading 'h1'
        h1 = children[0]
        if h1.tag == 'h1':
            h1.getparent().remove(h1)

        # remove first p if it is equal to the summary
        firstp = children[1]
        if firstp.tag == 'p' and firstp.text == article_xml.findtext('article_abstract'):
            firstp.getparent().remove(firstp)

        # remove last tag if it is the author
        lastp = children[-1]
        # article_author has been capitalized so compare lowers
        if lastp.tag == 'p' and (lastp.text and
                                 lastp.text.lower().strip() == article_xml.findtext('article_author').lower()):
            lastp.getparent().remove(lastp)

        # find subtitles, if text's length is < 50 characters, we consider it is a subtitle
        for child in children:
            if child.text and len(child.text) <= 50:
                child.tag = 'h5'

        stringified = ''.join([lxml.html.tostring(x, encoding='unicode', pretty_print=True, method='xml')
                              for x in tree.iterchildren()])
        return stringified

    def _capitalize_author(self, author):
        """Make sure we have Gauthier Bastien, not GAUTHIER BASTIEN or whatever."""
        res = [name.capitalize() for name in author.split(' ')]
        return ' '.join(res)

    def get_articles_xml(self, folder_id, publications):
        """ """
        # get every versions for the folder_id
        version_ids = self._get_versions_for(folder_id)
        # instanciate 'xml-to-plone' once
        xml_to_plone = self.context.restrictedTraverse('@@xml-to-plone')
        # now get articles by version
        res = []
        for version_id in version_ids:
            articles = self._get_articles_for(folder_id, version_id)
            for article in articles:
                article_infos = article['INFO']
                article_id = article_infos.get('ID')
                article_xml = ElementTree.Element("article", {'id': article_id})
                # XXX not used?
                ElementTree.SubElement(article_xml, "article_index").text = '?'
                ElementTree.SubElement(article_xml, "article_pubid").text = article_infos.get('PUBLICATIONIDS')
                ElementTree.SubElement(article_xml, "article_publication").text = article_infos['PUBLICATIONNAME']
                ElementTree.SubElement(article_xml, "article_date").text = article_infos.get('ISSUEDATE')
                article_title = article_infos.get('TITLE').replace('&amp;discReturn;&amp;discReturn;', '')
                if article_title.isupper():
                    article_title = article_title.capitalize()
                ElementTree.SubElement(article_xml, "article_title").text = article_title

                ElementTree.SubElement(article_xml, "article_abstract").text = article_infos.get('SUMMARY')
                ElementTree.SubElement(article_xml, "article_page").text = article_infos.get('PAGENR')
                # XXX not used?
                ElementTree.SubElement(article_xml, "article_mode").text = '?'
                # XXX not used?
                ElementTree.SubElement(article_xml, "article_price").text = '0'
                ElementTree.SubElement(article_xml, "article_folder").text = folder_id

                # do an additional query to ('/articledata') to try to
                # get the 'author' in case it was empty
                author = article_infos.get('AUTHOR')
                external_id = article_infos.get('EXTERNALID')
                if external_id and not author:
                    author = self._find_author(external_id)
                ElementTree.SubElement(article_xml, "article_author").text = \
                    author and self._capitalize_author(author) or ''

                # if article was not already managed, we used articles_data=true and we have 'ARTICLEDATA'
                # either, retrieve it from current metadatas.xml
                if 'ARTICLEDATA' in article_infos:
                    article_words = str(article_infos['ARTICLEDATA']['WORDCOUNT'])
                    articleHTML = self._clean_html(article_infos['ARTICLEDATA']['HTML'], article_xml)
                else:
                    article_words = xml_to_plone._get_article_information(folder_id, article_id)['article_words']
                    articleHTML = ''
                ElementTree.SubElement(article_xml, "article_words").text = article_words

                clipimg = article_infos['CLIPIMG']
                pdf_path = clipimg and clipimg + '&type=pdf' or ''
                res.append((article_xml, articleHTML, pdf_path))
        return res

    def _find_author(self, external_id):
        """ """
        author = ''
        # XXX change after
        return author
        article_data = self._send_json_request(path='/articledata/' + external_id)
        if 'RESPONSE' not in article_data:
            return author
        article_data = article_data['RESPONSE']['RESULTS']
        # if not author, use the 'persons' and check if last person is also <p>Prenom Nom</p>
        # at the the end of the article HTML
        persons = article_data[1]['persons']['persons']
        if persons:
            last_person = persons['item'][-1].strip() or ''
            # we will get a list of strings that are the HTML paragraphs but without the HTML <p> tag
            articleXMLBody = \
                article_data[0]['articleXML']['article.published']['body']['body.content']['body.p']['p']
            try:
                if articleXMLBody and articleXMLBody[-1].strip() == last_person:
                    author = last_person
            except Exception:
                self._verbose('Error finding author for %s (%s)' % (external_id, str(exc)))
        return author

    def _verbose(self, message, error=False, force=False, folder_id='', article_id=''):
        """
          To be used only on the test site
          print the message when  - force == True
                                  - FOLDER_TO_PRINT and ARTICLE_TO_PRINT are not null
                                  - FOLDER_TO_PRINT is not null and current folder_id == FOLDER_TO_PRINT
                                  - ARTICLE_TO_PRINT is not null and current article_id == ARTICLE_TO_PRINT
          logger.info() or logger.error() is used following the error parameter
        """
        #  print_soap_request = PRINT_SOAP_REQUEST
        #  pp = getToolByName(self,'portal_properties')
        #  if hasattr(pp, 'cedes_properties'):
        #    if pp.cedes_properties.hasProperty('print_soap_request'):
        #      print_soap_request = pp.cedes_properties.print_soap_request
        if not PRINT_GOPRESS_REQUEST:
            return False

        print_method = logger.info
        if error:
            print_method = logger.error

        if force:
            print_method(message)
        elif FOLDER_TO_PRINT and ARTICLE_TO_PRINT:
            print_method(message)
        elif FOLDER_TO_PRINT and folder_id == FOLDER_TO_PRINT:
            print_method(message)
        elif ARTICLE_TO_PRINT and article_id == ARTICLE_TO_PRINT:
            print_method(message)
        return True

    def _download_pdf(self, pdf_path):
        """ """
        # avoid TypeError: must be string or buffer, not None
        # see ticket http://trac-cedes.goforweb.be/ticket/580
        if not pdf_path:
            return ("nopdf", b'')
        else:
            res = self._send_json_request(path=pdf_path, return_as_raw=True)
        if res.strip().endswith(b"%%EOD"):
            res = res.replace("%%EOD", "%%EOF")
        return ("pdf", res)

    def _test_pdf(self, pdfFile):
        """ test Pdf file with pyPdf """
        try:
            temp = open(pdfFile, "rb")
            PdfFileReader(temp)
            temp.close()
            return ''
        except utils.PdfReadError:
            return "pdfreadererror %s" % msg
        except Exception:
            return "other %s" % msg

    def _fix_eof_pdf(self, pdfFile):
        """ fix pypdf error in pdf: ERROR: EOF marker not found """
        try:
            fileOpen = file(pdfFile, 'rb')
            tempInfo = fileOpen.read()
            fileOpen.close()
            fileOpen = open(pdfFile, 'wb')
            pos = tempInfo.rfind('%%EOF')
            length = len(tempInfo)
            if pos != -1:
                # removing trailing characters after %%EOF
                if (length-pos) < 20:
                    fileOpen.write(tempInfo[:pos+5])
            else:
                # removing trailing % because %%%EOF is not correct
                while tempInfo[-1] == '%':
                    tempInfo = tempInfo[:-1]
                fileOpen.write(tempInfo)
                fileOpen.write('%%EOF')
            fileOpen.close()
            return ''
        except Exception:
            return 'Unable to open file: %s with error: %s' % (pdfFile, str(e))

    def _treat_html_pdf(self, folder_id, article_id, articleHTML, pdf_path, force=0):
        """ """
        down_status = {'new_art': False,
                       'errors': [],
                       'warns': []}
        article_html_path = os.path.join(GOPRESS_PATH, folder_id, article_id + '.html')
        if force == 1 or not os.path.exists(article_html_path) or os.path.getsize(article_html_path) == 0:
            down_status['new_art'] = True
            if articleHTML is None:
                # self._verbose("no html: folderid=%s, articleid=%s"%(folder_id, article_id), error=True, force=True)
                self._verbose("no html: folderid=%s, articleid=%s" % (folder_id, article_id),
                              error=True, folder_id=folder_id, article_id=article_id)
                articleHTML = ''
            htmlfile = codecs.open(article_html_path, 'w', 'utf-8')
            htmlfile.write(articleHTML)
            htmlfile.close()

        article_pdf_path = os.path.join(GOPRESS_PATH, folder_id, article_id + '.pdf')
        article_largepdf_path = os.path.join(GOPRESS_PATH, folder_id, article_id + '.pdf.large')
        article_nopdf_path = os.path.join(GOPRESS_PATH, folder_id, article_id + '.nopdf')
        article_error_path = os.path.join(GOPRESS_PATH, folder_id, article_id + '.error')

        # removes the error file if previous error occured
        if os.path.exists(article_error_path):
            os.remove(article_error_path)
            force = 1

        # tries to download if no download yet
        if force == 1 or (not os.path.exists(article_largepdf_path) and
                          not os.path.exists(article_nopdf_path)):
            articlePDF = self._download_pdf(pdf_path)

            if articlePDF[0] == 'nopdf':
                pdffile = open(article_nopdf_path, 'w')
                pdffile.close()
            elif articlePDF[0] == 'pdf':
                pdffile = open(article_largepdf_path, 'wb')
                pdffile.write(articlePDF[1])
                pdffile.close()
                # try to open the PDFFile with PDF Reader, if we cannot do it, insert an error message
                err = self._test_pdf(article_largepdf_path)
                if err == 'pdfreadererror EOF marker not found':
                    # first keeping original
                    try:
                        orig = article_largepdf_path.replace(".pdf", ".orig.pdf")
                        if not os.path.exists(orig):
                            shutil.copyfile(article_largepdf_path, orig)
                    except Exception:
                        logger.error("Cannot copy '%s' to '%s': '%s'" % (article_largepdf_path, orig, msg))
                    err2 = self._fix_eof_pdf(article_largepdf_path)
                    if not err2:
                        err = self._test_pdf(article_largepdf_path)
                        if not err:
                            down_status['warns'].append("PDF corrigé :-)")
                        else:
                            # clean isn't good, we get back the original and remove copy
                            try:
                                shutil.copyfile(orig, article_largepdf_path)
                                os.remove(orig)
                            except Exception:
                                logger.error("Cannot copy '%s' to '%s': '%s'" % (orig, article_largepdf_path, msg))
                    else:
                        logger.error(err2)
                if err:
                    # os.remove(article_largepdf_path)
                    pdffile = open(article_error_path, 'w')
                    pdffile.write("PDF non conforme (groupement impossible): %s" % err)
                    pdffile.close()
                    down_status['errors'].append("PDF non conforme")
                else:
                    # no error, produce the light PDF
                    subprocess.call(GS_COMMAND % (article_pdf_path, article_largepdf_path), shell=True)
            else:  # if articlePDF[0] == 'error'
                pdffile = open(article_error_path, 'w')
                pdffile.write(articlePDF[1])
                pdffile.close()
                down_status['errors'].append("Problème PB")
        return down_status

    # copy the file in path with eventually date suffix
    def _backup_GP(self, filepath, path, suffix=False):
        """ """
        if not os.path.exists(filepath):
            logger.error("Error in backupPB: file to backup doesn't exist '%s'" % filepath)
            return
        if not os.path.exists(path):
            os.makedirs(path)
        import time
        filename = os.path.basename(filepath)
        if suffix:
            filename = "%s.%s" % (time.strftime('%Y%m%d%H%M%S',
                                                time.localtime(os.path.getmtime(filepath))),
                                  filename)
        dest = os.path.join(path, filename)
        try:
            shutil.copyfile(filepath, dest)
        except Exception:
            logger.error("Cannot copy '%s' to '%s': '%s'" % (filepath, dest, msg))


class XmlToPloneView(BrowserView):
    """
      This manage functionnality around xml_to_plone
    """
    def getFoldersInformation(self):
        res = []
        create_xml_file()
        xmlTree = ElementTree.parse(GOPRESS_XML_FILE_PATH)
        root = xmlTree.getroot()
        for element in root.findall('folder'):
            # calculate the price of a folder
            folder_price = 0
            for article in element.findall('article'):
                folder_price += float(article.findtext('article_price'))

            res.append({
                'folder_id': element.get('id'),
                'folder_name': element.findtext('folder_name'),
                # 'description': element.findtext('description'),
                'folder_articlecount': element.findtext('folder_articlecount'),
                'folder_price': folder_price,
                })
        return res

    # @returns List of dictionary representing all articles of folder folderId
    def getArticlesInformation(self, folderId):
        res = []
        create_xml_file()
        xmlTree = ElementTree.parse(GOPRESS_XML_FILE_PATH)
        root = xmlTree.getroot()
        folder = None
        for element in root.findall('folder'):
            if element.get('id') == folderId:
                folder = element
        if folder is None:
            return res
        for article in folder.findall('article'):
            article_pdf = 'error'
            article_pdf_error = ''
            article_pdf_path = os.path.join(GOPRESS_PATH, folderId, article.get('id') + '.pdf')
            article_nopdf_path = os.path.join(GOPRESS_PATH, folderId, article.get('id') + '.nopdf')
            article_error_path = os.path.join(GOPRESS_PATH, folderId, article.get('id') + '.error')
            if os.path.exists(article_pdf_path):
                article_pdf = 'oui'
            if os.path.exists(article_nopdf_path):
                article_pdf = 'non'
            if os.path.exists(article_error_path):
                # article_pdf = 'error'
                article_pdf_error = open(article_error_path, 'r').read()
            article_html_path = os.path.join(GOPRESS_PATH, folderId, article.get('id') + '.html')
            empty_html = False
            if os.path.exists(article_html_path) and os.path.getsize(article_html_path) == 0:
                empty_html = True

            articleId = article.get('id')
            article_title = ''
            article_html_metadata_path = os.path.join(GOPRESS_PATH, folderId, articleId + '.html.metadata')
            if os.path.exists(article_html_metadata_path):
                xmlTree = ElementTree.parse(article_html_metadata_path)
                root = xmlTree.getroot()
                article_title = root.findtext('article_title', '')

            res.append({
                'article_id': articleId,
                'article_title': article.findtext('article_title') and
                article.findtext('article_title') or (article_title and '=! %s !=' % article_title or ''),
                'article_pubid': article.findtext('article_pubid'),
                'article_publication': article.findtext('article_publication'),
                'article_words': article.findtext('article_words'),
                'article_page': article.findtext('article_page'),
                'article_mode': article.findtext('article_mode'),
                'article_date': article.findtext('article_date'),
                'article_price': article.findtext('article_price'),
                'article_pdf': article_pdf,
                'article_pdf_error': article_pdf_error,
                'no_html': empty_html,
                })
        return res

    def _get_article_information(self, folderId, articleId):
        """ """
        create_xml_file()
        xmlTree = ElementTree.parse(os.path.join(GOPRESS_PATH, "metadatas.xml"))
        root = xmlTree.getroot()
        for article in root.iter(tag='article'):
            if article.get('id') == articleId:
                return {
                    'article_id': article.get('id'),
                    'article_title': article.findtext('article_title'),
                    'article_pubid': article.findtext('article_pubid', ''),
                    'article_publication': article.findtext('article_publication', ''),
                    'article_words': article.findtext('article_words', ''),
                    'article_page': article.findtext('article_page', ''),
                    'article_mode': article.findtext('article_mode', ''),
                    'article_date': article.findtext('article_date', ''),
                    'article_price': article.findtext('article_price', ''),
                    'article_abstract': article.findtext('article_abstract', ''),
                    'article_author': article.findtext('article_author', ''),
                }
        return None

    def upload_article(self, folderId, articleId):
        """ """
        article_info = self._get_article_information(folderId, articleId)
        # html
        if os.path.exists(os.path.join(GOPRESS_PATH, folderId, articleId + '.html.clean.html')):
            article_html = open(os.path.join(GOPRESS_PATH, folderId, articleId + '.html.clean.html'), 'r')
        else:
            article_html = open(os.path.join(GOPRESS_PATH, folderId, articleId + '.html'), 'r')
        article_html_data = article_html.read()
        article_html.close()
        # file
        article_pdf = os.path.join(GOPRESS_PATH, folderId, articleId + '.pdf')
        article_pdf_data = None
        if os.path.exists(article_pdf):
            article_pdf = open(article_pdf, 'rb')
            article_pdf_data = article_pdf.read()
            article_pdf.close()

        createContentInContainer(
            self.context,
            "ArticlePayant",
            id=articleId,
            title=article_info['article_title'],
            description=article_info['article_abstract'],
            cr_classification=[],
            cr_author=article_info['article_author'],
            cr_periodical=article_info['article_publication'],
            cr_words_nb=article_info['article_words'],
            cr_periodical_pp=article_info['article_page'],
            cr_date=datetime.fromisoformat(article_info['article_date']),
            file=NamedBlobFile(article_pdf_data, filename=articleId + '.pdf'),
            cr_html_preview=richtextval(article_html_data))

    def merge_and_upload_articles(self,
                                  article_id,
                                  articles_and_folder_ids,
                                  option='htmlpdf',
                                  pb_folder=GOPRESS_PATH):
        """ """
        # merging the html content
        article_html = ""
        article_count = 0
        merged_authors = ''
        merged_pages = []
        for item_order, item_article_id, item_folder_id in articles_and_folder_ids:
            item_info = self._get_article_information(item_folder_id, item_article_id)
            # if not first, insert title
            if article_count > 0:
                article_html += '<h1 class="documentFirstHeading">' + \
                    self._get_article_information(item_folder_id, item_article_id)['article_title'] + \
                    '</h1>'

            # concatenate authors
            if item_info['article_author']:
                if not merged_authors:
                    merged_authors = item_info['article_author']
                elif item_info['article_author'] not in merged_authors:
                    merged_authors += ', %s' % item_info['article_author']

            # concatenate pages
            if item_info['article_page']:
                for page in item_info['article_page'].split(','):
                    if page not in merged_pages:
                        merged_pages.append(page.strip())

            # if HTML has been cleaned, use this one
            if os.path.exists(os.path.join(pb_folder, item_folder_id, item_article_id + '.html.clean.html')):
                html_file = open(os.path.join(pb_folder, item_folder_id, item_article_id + '.html.clean.html'), 'r')
            else:
                html_file = open(os.path.join(pb_folder, item_folder_id, item_article_id + '.html'), 'r')
            article_html += html_file.read()
            html_file.close()
            # if no 'html' in option, we only take the first page
            if not(option.startswith('html')):
                break
            article_count += 1

        # merging the pdf content
        if option.endswith('pdf'):
            article_pdf = PdfFileWriter()
            no_double_check = []
            article_pdf_string = BytesIO()
            for item_order, item_article_id, item_folder_id in articles_and_folder_ids:
                pdf_path = os.path.join(pb_folder, item_folder_id, item_article_id + '.pdf')
                if os.path.exists(pdf_path):
                    pdf_file = open(pdf_path, 'rb')
                    pdf_file_header = pdf_file.read(10240)
                    pdf_file.seek(0, 2)  # end of file
                    length = pdf_file.tell()
                    jump = (length > 10240 and length-10240 or length)
                    pdf_file.seek(jump)  # 10240 back from end of file
                    pdf_file_footer = pdf_file.read()
                    pdf_file.seek(0)  # beginning of file
                    # we check if we already read this file by comparing beginning and end of files
                    if (pdf_file_header, pdf_file_footer) not in no_double_check:
                        no_double_check.append((pdf_file_header, pdf_file_footer))
                        pdf_file_reader = PdfFileReader(pdf_file)
                        for page in pdf_file_reader.pages:
                            article_pdf.addPage(page)
                        article_pdf.write(article_pdf_string)
                        pdf_file.close() #KIM we cannot close the file before the stream is written
            del no_double_check
        else:  # do not group the pdf
            item = articles_and_folder_ids[0]
            pdf_path = os.path.join(pb_folder, item[2], item[1] + '.pdf')
            if os.path.exists(pdf_path):
                article_pdf_string = open(pdf_path, 'rb')
            else:
                article_pdf_string = BytesIO()
        article_pdf_string.seek(0)
        article_pdf_data = article_pdf_string.read()
        article_pdf_string.close()
        # uploading the article
        article_info = self._get_article_information(articles_and_folder_ids[0][2],
                                                     articles_and_folder_ids[0][1])
        createContentInContainer(
            self.context,
            "ArticlePayant",
            id=article_id,
            title=article_info['article_title'],
            description=article_info['article_abstract'],
            cr_author=merged_authors and merged_authors or article_info['article_author'],
            cr_periodical=article_info['article_publication'],
            cr_words_nb=article_info['article_words'],
            cr_periodical_pp=merged_pages and ','.join(merged_pages) or article_info['article_page'],
            cr_date=datetime.fromisoformat(article_info['article_date']),
            file=NamedBlobFile(article_pdf_data, filename=article_id + '.pdf'),
            cr_html_preview=richtextval(article_html))


class DownloadArticlePDFView(BrowserView):
    """
      This manage functionnality that download a PDF of an article
    """

    def __call__(self, folderId, articleId, large=False):
        """ """
        article_pdf = os.path.join(GOPRESS_PATH, folderId, articleId + '.pdf')
        if large:
            article_pdf += '.large'
        if os.path.exists(article_pdf):
            article_pdf = open(article_pdf, 'rb')
            content = article_pdf.read()
            article_pdf.close()
            self.request.RESPONSE.setHeader("Content-Disposition", "attachment; filename=%s.pdf" % articleId)
            self.request.RESPONSE.setHeader("Content-Type", "application/pdf")
            self.request.RESPONSE.setHeader("Cache-Control", "no-store")
            self.request.RESPONSE.setHeader("Pragma", "no-cache")
            return content
        return 'No PDF'
