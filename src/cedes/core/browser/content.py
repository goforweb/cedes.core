# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 by GoForWeb.be
#
# GNU General Public License (GPL)
#

from cedes.core.utils import provoke_unauthorized
from plone import api
from plone.dexterity.browser.view import DefaultView


class EmailContentView(DefaultView):
    """ """

    def update(self):
        super(EmailContentView, self).update()
        self.member = api.user.get_current()
        if self.member.has_role('Anonymous'):
            provoke_unauthorized()
        if self.member.is_manager() and \
           getattr(self.context, '_email_sent_date', None) is not None:
            api.portal.show_message(
                'E-mail envoyé le {0}'.format(
                    self.context._email_sent_date.strftime('%d/%m/%Y (%H:%M)')),
                request=self.request, type="warning")


class PointView(DefaultView):
    """ """
