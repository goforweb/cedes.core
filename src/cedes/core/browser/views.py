# -*- coding: utf-8 -*-

from AccessControl import Unauthorized
from Acquisition import aq_inner
from DateTime import DateTime
from io import StringIO
from plone import api
from plone.app.layout.navigation.interfaces import INavtreeStrategy
from plone.app.layout.navigation.navtree import buildFolderTree
from plone.batching import Batch
from plone.formwidget.namedfile.widget import Download as fnw_Download
from plone.memoize.view import memoize
from Products.CMFPlone.browser.navigation import CatalogSiteMap
from Products.CMFPlone.browser.navtree import SitemapQueryBuilder
from Products.CMFPlone.browser.sitemap import SitemapView
from Products.Five import BrowserView
from zope.component import getMultiAdapter


class CommonResultListingView(BrowserView):
    """
      This manage the elements listed using common result display
    """
    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.portal = api.portal.get()
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
          Find out what search we have to perform as this is
          a common view used to perform several searches.
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
        if contextLayout in ['listing_view']:
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


class ContextCatalogSiteMap(CatalogSiteMap):
    """ """
    def siteMap(self):
        context = aq_inner(self.context)

        queryBuilder = SitemapQueryBuilder(context)
        query = queryBuilder()

        strategy = getMultiAdapter((context, self), INavtreeStrategy)

        # XXX begin changes by cedes.core
        query['path'] = {'query': '/'.join(context.getPhysicalPath()), 'depth': 3}
        query['portal_type'] = ['Theme']
        query['exclude_from_nav'] = False
        # path to 'plan'
        strategy.rootPath = '/'.join(context.aq_parent.getPhysicalPath())
        # XXX end changes

        return buildFolderTree(context, obj=context,
                               query=query, strategy=strategy)


class ContextSitemapView(SitemapView):
    """ """

    def __init__(self, context, request):
        """ """
        super(ContextSitemapView, self).__init__(context, request)
        portal_url = api.portal.get_tool('portal_url')
        self.portal = portal_url.getPortalObject()
        self.portal_url = self.portal.absolute_url()

    def createSiteMap(self, context):
        # XXX begin changes by cedes.core
        # context = aq_inner(self.context)
        # XXX end changes

        view = getMultiAdapter((context, self.request),
                               name='sitemap_builder_view')
        data = view.siteMap()
        return self._renderLevel(children=data.get('children', []))


class ArticlePayantDownload(fnw_Download):
    """Make sure access to ArticlePayant file is controled."""

    def __call__(self):
        can_download = True
        parent = self.context.__parent__.context
        if parent.portal_type in ['ArticlePayant']:
            member = api.user.get_current()
            can_download = member.check_viewable(parent.UID())
        if can_download:
            return super(ArticlePayantDownload, self).__call__()
        else:
            raise Unauthorized


class CeDESNightTasks(BrowserView):
    """ """

    def __call__(self):
        ''' '''
        out = StringIO()
        now = DateTime()

        for member in api.user.get_users():
            member_id = member.getId()
            if member.send_no_login_notification(now=now):
                out.write("%s : rappel pas de login depuis 3 jours envoyé" % member_id)

            creditState = member.reset_expired_credit(now=now)
            if creditState == 1:
                out.write("%s : rappel crédits expirés envoyé et nouveau status CeDES Free" %  member_id)
            if creditState == 2:
                out.write("%s : crédits expirés, facture en attente" % member_id)

            if member.send_expiration_reminder(now=now, days=14):
                out.write("%s : rappel expiration des crédits dans 14 jours envoyé" % member_id)

            res = member.retry_bill_credits()
            if res is True:
                out.write("%s : données envoyées à la comptabilité pour facture/note de crédit" % member_id)
            if res is False:
                out.write("%s : nouvelle tentative d'envoi à la comptabilité échoué" % member_id)

            res = member.send_payment_reminder(now=now, days=10)
            if res is True:
                out.write("%s : rappel paiement envoyé" % member_id)
            if res is False:
                out.write("%s : impossible de se connecter à la comptabilité pour joindre "
                          "la facture au rappel de paiement" % member_id)

            if member.cancel_100_pc(now=now, days=30):
                out.write("%s : annulation de la facture après 30 jours pour cause "
                          "de non paiement. Devient cedes Free si balance nulle." % member_id)

        res = out.getvalue()
        if not res:
            res = "Aucune action à effectuer"

        #skintool = getToolByName(self, 'portal_skins')
        #mailHost = getToolByName(self, 'MailHost')
        #email = skintool.cedes_emails.crontasks_result(request=self.REQUEST, res=res, startdate=now, enddate=DateTime())
        #mailHost.send(email.encode('utf-8'))

        return res
