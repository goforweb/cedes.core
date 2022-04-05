# -*- coding: utf-8 -*-

from cedes.core import logger
from cedes.core.browser.member import get_member
from plone.app.contenttypes.browser.folder import FolderView
from plone.app.users.browser.account import AccountPanelForm
from plone.app.users.browser.userdatapanel import UserDataPanel
from plone.app.z3cform.inline_validation import InlineValidationView
from z3c.form.interfaces import HIDDEN_MODE

import json


class CedesFolderView(FolderView):
    """ """

    @property
    def no_items_message(self):
        """Do not display the message 'There is no element in this folder.'"""
        return ''


# monkey patch AccountPanel label, displayed at top of my preferences/password forms

@property
def label(self):
    return self.member.Title()


AccountPanelForm.label = label
logger.info("Monkey patching plone.app.users.account.AccountPanelForm (label)")


class CeDESUserDataPanel(UserDataPanel):
    """ """

    def _update(self):
        self.member = get_member(self.request)

    def __call__(self):
        """ """
        self._update()
        return super(CeDESUserDataPanel, self).__call__()

    def updateWidgets(self):
        """Hide "bill" fields to member if it is "CeDES Free"."""

        super(CeDESUserDataPanel, self).updateWidgets()
        # if member_type is "Free", hide the bill_* fields
        if not self.member.has_role("Manager") and \
           self.member.get_member_type() == "CeDES Free":
            for w in self.widgets:
                if w.startswith('bill'):
                    self.widgets[w].mode = HIDDEN_MODE


class CeDESInlineValidationView(InlineValidationView):
    """Disable the z3cform inline validation."""

    def __call__(self, fname=None, fset=None):
        """ """
        self.request.response.setHeader('Content-Type', 'application/json')
        return json.dumps({'errmsg': ''})
