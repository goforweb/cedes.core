# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 by GoForWeb.be
#
# GNU General Public License (GPL)
#

from cedes.core import logger
from collections import OrderedDict
from DateTime import DateTime
from plone import api
from plone.app.textfield.value import RichTextValue
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import safe_unicode

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
                                 if x in (string.ascii_letters+string.digits)).lower()
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
