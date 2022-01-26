# -*- coding: utf-8 -*-

from cedes.core.utils import normalize_data
from DateTime import DateTime
from eea.facetednavigation.browser.app.query import FacetedQueryHandler
from plone import api
from Products.Five import BrowserView

import re


class FacetedThemeView(BrowserView):
    """ """

    def __init__(self, context, request):
        super(FacetedThemeView, self).__init__(context, request)
        portal_url = api.portal.get_tool('portal_url')
        self.portal = portal_url.getPortalObject()
        self.portal_url = self.portal.absolute_url()

    def is_search(self):
        """ """
        form = self.request.form
        concatened_keys = ''.join(form.keys())
        return bool(re.findall(r'c\d+\[]', concatened_keys))

    def may_search(self):
        """ """
        membership = api.portal.get_tool('portal_membership')
        member = membership.getAuthenticatedMember()
        return (not(member.is_cedes_free()) or
                (member.is_cedes_free() and
                 member.get_first_login_time() + 7 > DateTime()))

    def search_terms(self):
        """ """
        return [term for term in self.request.form.get('c3[]', '').split(' ')]


class ThemeFacetedQueryHandler(FacetedQueryHandler):
    """ """

    def criteria(self, sort=False, **kwargs):
        """Normalize data used for SearchableText catalog index."""
        query = super(ThemeFacetedQueryHandler, self).criteria(sort, **kwargs)

        if 'SearchableText' in query:
            normalized_query = normalize_data(query['SearchableText']['query'])
            # we have to add back the ending '*' if necessary
            if query['SearchableText']['query'].endswith('*'):
                normalized_query = normalized_query + '*'
            query['SearchableText']['query'] = normalized_query
        # force sort_order descending
        if 'sort_order' in query:
            query['sort_order'] = 'descending'
        return query
