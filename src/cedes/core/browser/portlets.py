# -*- coding: utf-8 -*-

from cedes.core import utils
from plone import api
from Products.Five import BrowserView


class PortletRecent(BrowserView):
    """ """

    def _update(self):
        """ """
        self.portal = api.portal.get()
        self.portal_url = self.portal.absolute_url()
        self.member = api.user.get_current()
        self.is_anon = self.portal.portal_membership.isAnonymousUser()

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
