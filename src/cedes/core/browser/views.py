# -*- coding: utf-8 -*-

from plone.batching import Batch
from plone.memoize.view import memoize
from Products.Five import BrowserView
from zope.component import getMultiAdapter


class CommonResultListingView(BrowserView):
    """
      This manage the elements listed using common result display
    """
    def __init__(self, context, request):
        self.context = context
        self.request = request
        portal_state = getMultiAdapter((self.context, self.request), name=u'plone_portal_state')
        self.portal = portal_state.portal()
        self.full = self.context.getLayout() == 'folder_full_listing'

    def performSearch(self, b_size=30, b_start=0):
        """
          Perform a specific search and return the result batched.
          This view is used for common results that perform several kind of search.
          We know what kind of search to perform with given p_search_for.
        """
        result = []
        search_for = self._findSearchFor()
        if search_for == 'dossier_view':
            result = self.context.getFolderContents({'portal_type': ['ArticleGratuit',
                                                                     'ArticlePayant',
                                                                     'SiteInternet',
                                                                     'Statistiques',
                                                                     'Audio',
                                                                     'Video',
                                                                     'Cederom',
                                                                     'Bibliographie',
                                                                     'SequenceApprentissage',
                                                                     'DossierStructure',
                                                                     'Folder'],
                                                     'sort_on': 'getObjPositionInParent'},
                                                    batch=False)
        elif search_for == 'theme_view':
            result = self.searchForThemeView()
        elif search_for == 'point_view':
            # query using portal_catalog to return brains
            uids = self.context.getRawCf_resources()
            catalog = self.portal.portal_catalog
            brains = catalog(UID=uids)

            # sort brains by original uids order
            def getKey(item):
                return uids.index(item.UID)
            result = sorted(brains, key=getKey)
        elif search_for == 'recently_modified':
            result = self.context.getLatestEntries(sort_limit=20)
        elif search_for == 'folder_listing':
            result = self.context.getFolderContents({'portal_type': ['ArticleGratuit',
                                                                     'ArticlePayant',
                                                                     'SiteInternet',
                                                                     'Statistiques',
                                                                     'Audio',
                                                                     'Video',
                                                                     'Cederom',
                                                                     'Bibliographie',
                                                                     'SequenceApprentissage',
                                                                     'DossierStructure',
                                                                     'Folder'], },
                                                    batch=False)
        batch = Batch(result, b_size, b_start, orphan=1)
        return batch

    def _findSearchFor(self):
        """
          Find out what search we have to perform as this is a common view used to perform several searches.
        """
        contextPortalType = self.context.portal_type
        if contextPortalType == 'Theme':
            if not self.request['URL'].endswith('@@updated_search'):
                return 'theme_view'
        if contextPortalType == 'Point':
            return 'point_view'

        if self.request['URL'].endswith('recently_modified'):
            return 'recently_modified'

        contextLayout = self.context.getLayout()
        if contextLayout in ['folder_listing', 'folder_full_listing']:
            return 'folder_listing'
        if contextLayout == 'dossier_view':
            return 'dossier_view'

    @memoize
    def searchForThemeView(self):
        """
          Use an intermediate method to call Theme.getAssociatedResources so it can be
          memoized because it is called twice in the theme_view.
        """
        return self.context.get_associated_resources()

    def update_content(self):
        return self.context.restrictedTraverse('@@common-result-listing').index()
