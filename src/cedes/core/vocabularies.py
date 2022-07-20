# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 by GoForWeb.be
#
# GNU General Public License (GPL)
#

from cedes.core.config import CEDES_RESOURCE_TYPES
from cedes.core.config import COUNTRIES
from plone.app.vocabularies.principals import GroupsFactory
from plone.app.vocabularies.principals import PrincipalsFactory
from plone.app.vocabularies.principals import UsersFactory
from plone.memoize import ram
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
        portal_types = getToolByName(context, 'portal_types')
        for portal_type_name in CEDES_RESOURCE_TYPES:
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
                              u'Date d\'encodage sur le CeDES (toutes resources)'))
        res.append(SimpleTerm('positive_ratings', 'positive_ratings', u'Les plus aimées'))
        return SimpleVocabulary(res)


FacetedSortingVocabularyFactory = FacetedSortingVocabulary()


@implementer(IVocabularyFactory)
class CountriesVocabulary(object):
    """ """

    def __call__(self, context):
        res = []
        for country_code, country_name in COUNTRIES:
            res.append(SimpleTerm(country_code,
                                  country_code,
                                  country_name))
        return SimpleVocabulary(res)


CountriesVocabularyFactory = CountriesVocabulary()


# override principals/users/groups vocabularies to add caching
class CeDESPrincipalsFactory(PrincipalsFactory):

    def __call___cachekey(method, self, context, query=''):
        '''cachekey method for self.__call__.'''
        return query

    @ram.cache(__call___cachekey)
    def CeDESPrincipalsFactory__call__(self, context, query=''):
        return super(CeDESPrincipalsFactory, self).__call__(context, query)

    # do ram.cache have a different key name
    __call__ = CeDESPrincipalsFactory__call__


class CeDESUsersFactory(UsersFactory):

    def __call___cachekey(method, self, context, query=''):
        '''cachekey method for self.__call__.'''
        return query

    @ram.cache(__call___cachekey)
    def CeDESUsersFactory__call__(self, context, query=''):
        return super(CeDESUsersFactory, self).__call__(context, query)

    # do ram.cache have a different key name
    __call__ = CeDESUsersFactory__call__


class CeDESGroupsFactory(GroupsFactory):

    def __call___cachekey(method, self, context, query=''):
        '''cachekey method for self.__call__.'''
        return query

    @ram.cache(__call___cachekey)
    def CeDESGroupsFactory__call__(self, context, query=''):
        return super(CeDESGroupsFactory, self).__call__(context, query)

    # do ram.cache have a different key name
    __call__ = CeDESGroupsFactory__call__
