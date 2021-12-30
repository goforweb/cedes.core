# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 by GoForWeb.be
#
# GNU General Public License (GPL)
#

from cedes.core.config import CEDES_RESSOURCE_TYPES
from Products.CMFCore.utils import getToolByName
from zope.interface import implementer
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary


@implementer(IVocabularyFactory)
class SearchableTypesVocabulary(object):
    """ """

    def __call__(self, context):
        res = []
        plone_utils = getToolByName(context, 'plone_utils')
        portal_types = getToolByName(context, 'portal_types')
        for portal_type_name in CEDES_RESSOURCE_TYPES:
            type_info = portal_types.get(portal_type_name)
            if type_info:
                res.append(
                    SimpleTerm(type_info.id, type_info.id, type_info.title))
        return SimpleVocabulary(res)


SearchableTypesVocabularyFactory = SearchableTypesVocabulary()


@implementer(IVocabularyFactory)
class FacetedSortingVocabulary(object):
    """ """

    def __call__(self, context):
        res = []
        res.append(SimpleTerm('cr_date',
                              'cr_date',
                              u'Date de parution (pour les articles)'))
        res.append(SimpleTerm('cr_first_classification_date_index',
                              'cr_first_classification_date_index',
                              u'Date d\'encodage sur le CeDES (toutes ressources)'))
        res.append(SimpleTerm('positive_ratings', 'positive_ratings', u'Les plus aimées'))
        return SimpleVocabulary(res)


FacetedSortingVocabularyFactory = FacetedSortingVocabulary()
