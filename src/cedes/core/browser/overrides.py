# -*- coding: utf-8 -*-

from cedes.core import logger
from cedes.core.browser.member import get_member
from cedes.core.browser.register import BillLabelProvider
from plone import api
from plone.app.contenttypes.browser.folder import FolderView
from plone.app.users.browser.account import AccountPanelForm
from plone.app.users.browser.userdatapanel import UserDataPanel
from plone.app.z3cform.inline_validation import InlineValidationView
from z3c.form.contentprovider import ContentProviders
from z3c.form.interfaces import HIDDEN_MODE
from z3c.form.interfaces import IFieldsAndContentProvidersForm
from zope.interface import implementer

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


@implementer(IFieldsAndContentProvidersForm)
class CeDESUserDataPanel(UserDataPanel):
    """ """
    contentProviders = ContentProviders()
    contentProviders['bill_label'] = BillLabelProvider
    contentProviders['bill_label'].position = 10

    def _update(self):
        self.member = get_member(self.request)

    def __call__(self):
        """ """
        self._update()
        return super(CeDESUserDataPanel, self).__call__()

    def updateWidgets(self):
        """Hide "bill" fields to member if it is "CeDES Free"."""
        is_manager = api.user.get_current().has_role("Manager")
        if is_manager:
            # move bill_label one position down because field member_type
            # is displayed for Manager
            self.contentProviders['bill_label'].position = 11
        else:
            self.contentProviders['bill_label'].position = 10

        super(CeDESUserDataPanel, self).updateWidgets()
        # if member_type is "Free", hide the bill_* fields excepted for Managers
        if not is_manager and \
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
