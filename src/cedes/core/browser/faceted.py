# -*- coding: utf-8 -*-

from DateTime import DateTime
from eea.facetednavigation.browser.app.query import FacetedQueryHandler
from cedes.core.utils import normalizeData
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import safe_unicode
from Products.Five import BrowserView

import re


class FacetedThemeView(BrowserView):
    """ """

    def __init__(self, context, request):
        super(FacetedThemeView, self).__init__(context, request)
        portal_url = getToolByName(context, 'portal_url')
        self.portal = portal_url.getPortalObject()
        self.portal_url = self.portal.absolute_url()

    def is_search(self):
        """ """
        form = self.request.form
        concatened_keys = ''.join(form.keys())
        return bool(re.findall(r'c\d+\[]', concatened_keys))

    def may_search(self):
        """ """
        return True
        membership = getToolByName(self.context, 'portal_membership')
        member = membership.getAuthenticatedMember()
        return (not(member.isCedesFree()) or (member.isCedesFree() and member.created() + 7 > DateTime()))

    def search_terms(self):
        """ """
        return [unicode(term, 'utf-8') for term in self.request.form.get('c3[]', '').split(' ')]


class ThemeFacetedQueryHandler(FacetedQueryHandler):
    """ """

    def criteria(self, sort=False, **kwargs):
        """Normalize data used for SearchableText catalog index."""
        query = super(ThemeFacetedQueryHandler, self).criteria(sort, **kwargs)

        if 'SearchableText' in query:
            normalized_query = normalizeData(safe_unicode(query['SearchableText']['query']))
            # we have to add back the ending '*' if necessary
            if safe_unicode(query['SearchableText']['query']).endswith('*'):
                normalized_query = normalized_query + '*'
            query['SearchableText']['query'] = normalized_query
        # force sort_order descending
        if 'sort_order' in query:
            query['sort_order'] = 'descending'
        return query
