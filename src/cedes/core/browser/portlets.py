# -*- coding: utf-8 -*-

from cedes.core import utils
from plone import api
from plone.app.portlets.portlets.navigation import Renderer as NavigationRenderer
from plone.app.portlets.portlets.recent import Renderer as RecentRenderer
from Products.CMFCore.utils import _checkPermission
from Products.Five import BrowserView


class PortletRecent(BrowserView):
    """ """

    def _update(self):
        """ """
        self.portal = api.portal.get()
        self.portal_url = self.portal.absolute_url()
        self.member = api.user.get_current()
        self.is_anon = self.portal.portal_membership.isAnonymousUser()
        self.is_cedes_free = not self.is_anon and self.member.is_cedes_free or False

    def available(self):
        """ """
        return not self.portal.portal_membership.isAnonymousUser() and \
            _checkPermission("View", self.portal.plan)

    def __call__(self):
        """ """
        self._update()
        return super(PortletRecent, self).__call__()

    def get_latest_entries(self, sort_limit=8):
        """ """
        return utils.get_latest_entries(sort_limit=sort_limit)

    def get_on_click(self, obj, onclick_action):
        """ """
        onclick = ''
        if (obj.portal_type == 'ArticlePayant' and not(self.is_anon)) or \
           (obj.portal_type == 'SequenceApprentissage' and not(self.is_anon) and
                self.member.is_cedes_free()):
            onclick = onclick_action
        return onclick


class PortletPlan(BrowserView):
    """ """

    def available(self):
        """ """
        return not self.portal.portal_membership.isAnonymousUser() and \
            _checkPermission("View", self.portal.plan)

    def _update(self):
        """ """
        self.portal = api.portal.get()
        self.portal_url = self.portal.absolute_url()

    def __call__(self):
        """ """
        self._update()
        return super(PortletPlan, self).__call__()


class BasePortletFolders(BrowserView):
    """A portlet that displays published folders of a specific folder at root of Plone."""

    # to be overrided
    main_folder_id = None

    def _update(self):
        """ """
        self.portal = api.portal.get()
        self.portal_url = self.portal.absolute_url()

    def __call__(self):
        """ """
        self._update()
        return super(BasePortletFolders, self).__call__()

    def available(self):
        """ """
        return not self.portal.portal_membership.isAnonymousUser() and \
            _checkPermission("View", self.portal.get(self.main_folder_id))

    def main_folder_title(self):
        """ """
        return self.portal.get(self.main_folder_id).Title()

    def get_folders(self):
        """ """
        catalog = api.portal.get_tool('portal_catalog')
        portal_path = "/".join(self.portal.getPhysicalPath())
        brains = catalog(
            portal_type='Folder',
            path={'query': portal_path + '/' + self.main_folder_id, 'depth': 1},
            sort_on='getObjPositionInParent')
        return brains


class PortletDossiers(BasePortletFolders):
    """ """

    main_folder_id = "dossiers-structures"


class PortletCedes(BasePortletFolders):
    """ """

    main_folder_id = "boite-a-outils"


class CedesNavigationRenderer(NavigationRenderer):
    """ """

    @property
    def available(self):
        member = api.user.get_current()
        if member.has_role('Anonymous') or not member.is_manager():
            return False
        return super(CedesNavigationRenderer, self).available


class CedesRecentRenderer(RecentRenderer):
    """ """

    @property
    def available(self):
        member = api.user.get_current()
        if member.has_role('Anonymous') or not member.is_manager():
            return False
        return super(CedesRecentRenderer, self).available
