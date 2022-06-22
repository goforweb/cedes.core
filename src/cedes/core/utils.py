# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 by GoForWeb.be
#
# GNU General Public License (GPL)
#

from AccessControl import Unauthorized
from cedes.core import logger
from cedes.core.config import EXTRA_MAIL_TO
from collections import OrderedDict
from DateTime import DateTime
from email.encoders import encode_base64
from email.header import Header
from email.mime.base import MIMEBase
from plone import api
from plone.app.textfield.value import RichTextValue
from plone.registry.interfaces import IRegistry
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.interfaces.controlpanel import IMailSchema
from Products.CMFPlone.utils import safe_unicode
from Products.Five import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.MailHost.interfaces import IMailHost
from zc.relation.interfaces import ICatalog
from zope.component import getUtility
from zope.globalrequest import getRequest
from zope.intid.interfaces import IIntIds

import string
import unicodedata


def normalize_data(data):
    """
      Normalize data, remove accents, quotes, capital letters and trailing 's'
    """
    data = safe_unicode(data)
    res = []
    charsToBlank = [u"'", u"-", u"\u2019", u"\n"]
    for char in charsToBlank:
        data = data.replace(char, ' ')
    for word in data.split(' '):
        normalizedWord = ''.join(x for x in unicodedata.normalize('NFKD', word)
                                 if x in (string.ascii_letters + string.digits)).lower()
        normalizedWord = normalizedWord.rstrip('s')
        normalizedWord = normalizedWord.rstrip('x')
        normalizedWord = normalizedWord.strip()
        res.append(normalizedWord)
    return ' '.join(res)


def get_modified_attrs(modified_event):
    """Useful in a IObjectModifiedEvent to get what fields were actually edited."""
    mod_attrs = [name for attr in modified_event.descriptions
                 for name in attr.attributes]
    return mod_attrs


def richtextval(text, mimeType=u"text/html", outputMimeType=u"text/x-html-safe"):
    """
        Return a RichTextValue to be stored in IRichText field
    """
    return RichTextValue(raw=text,
                         mimeType=mimeType,
                         outputMimeType=outputMimeType)


def gopress_stats(context, datefrom, dateto):
    """ """
    catalog = getToolByName(context, 'portal_catalog')
    datefrom = DateTime(datefrom)
    dateto = DateTime(dateto)
    query = {}
    query['cr_date'] = {'query': (datefrom, dateto),
                        'range': 'minmax'}
    query['portal_type'] = ('ArticlePayant', )
    logger.info('Query...')
    brains = catalog(cr_date={'query': (datefrom, dateto), 'range': 'minmax'},
                     portal_type='ArticlePayant',
                     sort_on='cr_date')
    logger.info('Done.')

    logger.info('Articles...')
    articles = OrderedDict()
    for brain in brains:
        articles[brain.UID] = {
            'count': 0,
            'path': brain.getPath(),
            'url': brain.getURL(),
            'title': brain.Title,
            'cr_date': brain.cr_date}
    logger.info('Done.')

    logger.info('Members...')
    mtool = getToolByName(context, 'portal_membership')
    for member in mtool.listMembers():
        for transaction_uid, cost, date in member.getTransactions():
            if transaction_uid in articles:
                articles[transaction_uid]['count'] = articles[transaction_uid]['count'] + 1
    logger.info('Done.')

    logger.info('Output...')
    # output
    output = []
    total = 0
    line = 1
    for uid in articles:
        output.append("{0}. <a href='{1}'>{2}</a> ({3}) : {4}".format(
            line, articles[uid]['url'], articles[uid]['title'],
            articles[uid]['cr_date'].strftime('%d/%m/%y'), articles[uid]['count']))
        line = line + 1
        total = total + articles[uid]['count']

    output.append("<p>Nombre d'articles payants : {0}".format(len(articles)))
    output.append("<p>Nombre d'acc&egrave;s total : {0}".format(total))
    logger.info('Done.')

    return output


def get_latest_entries(sort_limit=5):
    catalog = api.portal.get_tool('portal_catalog')
    # we use getCr_first_classification_date that is initialized only when a resource is classified
    res = list(catalog.unrestrictedSearchResults(
        portal_type=['ArticleGratuit',
                     'ArticlePayant',
                     'Audio',
                     'Video',
                     'SiteInternet',
                     'Statistiques',
                     'Cederom',
                     'Bibliographie',
                     'SequenceApprentissage'],
        review_state='published',
        cr_first_classification_date_index={
            'query': DateTime('01/01/1950'),
            'range': 'min'},
        sort_on='cr_first_classification_date_index',
        sort_order='reverse',
        sort_limit=sort_limit))
    return res


def add_page_message(portal, page_id, type="warning"):
    """ """
    # do not add message when clicking on 'Cancel' button of a form
    if 'form.buttons.cancel' in portal.REQUEST:
        return
    page = portal.pages.get(page_id)
    if page:
        msg = page.text.output
    else:
        msg = "Fichier '%s' manquant" % page_id
    api.portal.show_message(msg, request=portal.REQUEST, type=type)


def uuidsToCatalogBrains(uuids=[],
                         ordered=False,
                         query={},
                         check_contained_uids=False,
                         unrestricted=False):
    """ Given a list of UUIDs, attempt to return catalog brains,
        keeping original uuids list order if p_ordered=True.
        If p_check_contained_uids=True, if we do not find brains using the UID
        index, we will try to get it using the contained_uids index, used when
        subelements are not indexed."""

    catalog = api.portal.get_tool('portal_catalog')
    searcher = catalog.searchResults
    if unrestricted:
        searcher = catalog.unrestrictedSearchResults

    brains = searcher(UID=uuids, **query)

    if not brains and check_contained_uids and 'contained_uids' in catalog.Indexes:
        brains = searcher(contained_uids=uuids, **query)

    if ordered:
        # we need to sort found brains according to uuids
        def getKey(item):
            return uuids.index(item.UID)
        brains = sorted(brains, key=getKey)

    return brains


def uuidToCatalogBrain(uuid,
                       ordered=False,
                       query={},
                       check_contained_uids=False,
                       unrestricted=False):
    """Shortcut to call uuidsToCatalogBrains to get one single element."""
    res = uuidsToCatalogBrains(
        uuids=[uuid],
        ordered=ordered,
        query=query,
        check_contained_uids=check_contained_uids,
        unrestricted=unrestricted)
    if res:
        res = res[0]
    return res


def _contained_objects(obj, only_unindexed=False):
    """Return every elements contained in p_obj, incuding sub_elements.
       If p_only_unindexed=True, then we only return elements that are not indexed"""
    if only_unindexed and not IContainerOfUnindexedElementsMarker.providedBy(obj):
        return []

    def get_objs(container, objs=[]):
        for subcontainer in container.objectValues():
            if not only_unindexed or \
               (only_unindexed and subcontainer._getCatalogTool() is None):
                objs.append(subcontainer)
            get_objs(subcontainer, objs)
        return objs
    return get_objs(obj)


def uuidsToObjects(uuids=[], ordered=False, query={}, check_contained_uids=False, unrestricted=False):
    """ Given a list of UUIDs, attempt to return content objects,
        keeping original uuids list order if p_ordered=True.
        If p_check_contained_uids=True, if we do not find brains using the UID
        index, we will try to get it using the contained_uids index, used when
        subelements are not indexed. """

    brains = uuidsToCatalogBrains(uuids,
                                  ordered=not check_contained_uids and ordered or False,
                                  query=query,
                                  check_contained_uids=check_contained_uids,
                                  unrestricted=unrestricted)
    res = []
    if check_contained_uids:
        need_reorder = False
        for brain in brains:
            obj = brain._unrestrictedGetObject()
            if obj.UID() not in uuids:
                # it means we have a brain using a contained_uids
                for contained in _contained_objects(obj):
                    if contained.UID() in uuids:
                        need_reorder = True
                        res.append(contained)
            else:
                res.append(obj)
        if ordered and need_reorder:
            # need to sort here as disabled when calling uuidsToCatalogBrains
            def getKey(item):
                return uuids.index(item.UID())
            res = sorted(res, key=getKey)
    else:
        res = [brain._unrestrictedGetObject() for brain in brains]
    return res


def uuidToObject(uuid,
                 ordered=False,
                 query={},
                 check_contained_uids=False,
                 unrestricted=False):
    """Shortcut to call uuidsToObjects to get one single element."""
    res = uuidsToObjects(
        uuids=[uuid],
        ordered=ordered,
        query=query,
        check_contained_uids=check_contained_uids,
        unrestricted=unrestricted)
    if res:
        res = res[0]
    return res


def get_member(request):
    """ """
    userid = request.get('userid', None)
    current_user = api.user.get_current()
    if userid and not current_user.is_manager():
        raise Unauthorized
    return userid and api.portal.get_tool('portal_membership').getMemberById(userid) or current_user


def send_mail(subject,
              template_name,
              options={},
              mto=[],
              mfrom=None,
              attachments=[]):
    """ """
    registry = getUtility(IRegistry)
    mail_settings = registry.forInterface(IMailSchema, prefix='plone')

    def encode_mail_header(text):
        """ Encodes text into correctly encoded email header """
        return Header(safe_unicode(text), 'utf-8')

    def encoded_mail_sender():
        """ returns encoded version of Portal name <portal_email> """
        from_ = mail_settings.email_from_name
        mail = mail_settings.email_from_address
        return '"{}" <{}>'.format(encode_mail_header(from_), mail)

    mfrom = mfrom or encoded_mail_sender()
    # send to CeDES Managers when no mto given
    if not mto:
        if not isinstance(mto, (tuple, list)):
            mto = [mto]
        mto += EXTRA_MAIL_TO
    host = getUtility(IMailHost)
    encoding = registry.get('plone.email_charset', 'utf-8')
    view = BrowserView(api.portal.get(), getRequest())
    email = ViewPageTemplateFile('browser/templates/{0}.pt'.format(template_name))
    text = email(view, **options).encode(encoding)
    payload = text
    if attachments:
        from email.mime.multipart import MIMEMultipart
        from email.mime.base import MIMEBase
        from email.mime.text import MIMEText
        msg = MIMEMultipart()
        body = MIMEText(text, _charset=encoding)
        msg.attach(body)
        for attachment in attachments:
            if not isinstance(attachment, MIMEBase):
                raise Exception("utils.send_mail attachments must be MIMEBase instances")
            msg.attach(attachment)
        payload = msg
    # send email
    host.send(payload,
              mto=mto,
              mfrom=mfrom,
              subject=subject,
              charset=encoding)


def create_attachment(filetype, payload, filename):
    """ """
    # filetype is like "application/pdf"
    _maintype, _subtype = filetype.split('/')
    attachment = MIMEBase(_maintype, _subtype)
    attachment.set_payload(payload)
    encode_base64(attachment)
    attachment.add_header('Content-Disposition', 'attachment', filename=filename)
    return attachment


def provoke_unauthorized():
    raise Unauthorized


def get_intid(obj):
    """Return the intid of an object from the intid-catalog"""
    intids = getUtility(IIntIds)
    if intids is None:
        return
    # check that the object has an intid, otherwise there's nothing to be done
    try:
        return intids.getId(obj)
    except KeyError:
        # The object has not been added to the ZODB yet
        return


def get_relations(obj, attribute=None, backrefs=False):
    """Get any kind of references and backreferences"""
    int_id = get_intid(obj)
    if not int_id:
        return []

    relation_catalog = getUtility(ICatalog)
    if not relation_catalog:
        return []

    query = {}
    if attribute:
        # Constrain the search for certain relation-types.
        query['from_attribute'] = attribute

    if backrefs:
        query['to_id'] = int_id
    else:
        query['from_id'] = int_id

    return relation_catalog.findRelations(query)
