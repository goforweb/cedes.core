# -*- coding: utf-8 -*-

from AccessControl import Unauthorized
from Acquisition import aq_inner
from cedes.core.utils import send_mail
from DateTime import DateTime
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
            # we need to return brains...
            # we will get every path of relations and query it
            paths = [rel.to_path for rel in self.context.cf_resources]
            catalog = self.portal.portal_catalog
            brains = catalog(path={'query': paths, 'depth': 0})

            # sort brains by original paths order
            def getKey(item):
                return paths.index(item.getPath())
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
                                                                     'Folder',
                                                                     'EmailContent'], },
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

        # begin changes by cedes.core
        query['path'] = {'query': '/'.join(context.getPhysicalPath()), 'depth': 3}
        query['portal_type'] = ['Theme']
        query['exclude_from_nav'] = False
        # path to 'plan'
        strategy.rootPath = '/'.join(context.aq_parent.getPhysicalPath())
        # end changes by cedes.core

        return buildFolderTree(context, obj=context,
                               query=query, strategy=strategy)


class ContextSitemapView(SitemapView):
    """ """

    def __init__(self, context, request):
        """ """
        super(ContextSitemapView, self).__init__(context, request)
        self.portal = api.portal.get()
        self.portal_url = self.portal.absolute_url()

    def createSiteMap(self, context):
        # begin changes by cedes.core
        # context = aq_inner(self.context)
        # end changes by cedes.core

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

    def _get_last_execution(self):
        """Return the last time check was executed."""
        last_tasks_execution = getattr(self.context, '_last_tasks_execution', DateTime('1950/01/01'))
        return last_tasks_execution

    def _set_last_execution(self, now):
        """Set the last time check was executed."""
        setattr(self.context, '_last_tasks_execution', now)

    def __call__(self, check_period=True, force_execution=False):
        """ """
        if check_period and not force_execution:
            last = self._get_last_execution()
            now = DateTime()
            # period is in days
            period = now - last
            if (now.hour() == 4 and period < 0.5) or period < 1:
                return

        out = []
        now = DateTime()

        for member in api.user.get_users():
            member_id = member.getId()
            if member.send_no_login_notification(now=now):
                out.append("%s : rappel pas de login depuis 3 jours envoyé" % member_id)

            creditState = member.reset_expired_credit(now=now)
            if creditState == 1:
                out.append("%s : rappel crédits expirés envoyé et nouveau status CeDES Free" % member_id)
            if creditState == 2:
                out.append("%s : crédits expirés, facture en attente" % member_id)

            if member.send_expiration_reminder(now=now, days=14):
                out.append("%s : rappel expiration des crédits dans 14 jours envoyé" % member_id)

            res = member.retry_bill_credits()
            if res is True:
                out.append("%s : données envoyées à la comptabilité pour facture/note de crédit" % member_id)
            if res is False:
                out.append("%s : nouvelle tentative d'envoi à la comptabilité échoué" % member_id)

            res = member.send_payment_reminder(now=now, days=10)
            if res is True:
                out.append("%s : rappel paiement envoyé" % member_id)
            if res is False:
                out.append("%s : impossible de se connecter à la comptabilité pour joindre "
                           "la facture au rappel de paiement" % member_id)

            if member.cancel_100_pc(now=now, days=30):
                out.append("%s : annulation de la facture après 30 jours pour cause "
                           "de non paiement. Devient cedes Free si balance nulle." % member_id)

        if not out:
            out = "Aucune action à effectuer"
        out = "\n".join(out)

        # email notification for Managers
        send_mail(subject='CeDES - Résultat des tâches lancées la nuit',
                  template_name='mail_crontasks_result',
                  options={'out': out,
                           'startdate': now,
                           'enddate': DateTime()})

        self._set_last_execution(now)

        return out.replace('\n', '<br>')
