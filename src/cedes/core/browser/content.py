# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 by GoForWeb.be
#
# GNU General Public License (GPL)
#

from plone import api
from plone.dexterity.browser.view import DefaultView


class EmailContentView(DefaultView):
    """ """

    def update(self):
        super(EmailContentView, self).update()
        self.member = api.user.get_current()


class PointView(DefaultView):
    """ """
