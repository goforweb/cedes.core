# -*- coding: utf-8 -*-

from plone.app.users.browser.registered import RegisteredView


class CeDESRegisteredView(RegisteredView):

    def __call__(self, member_type):
        """ """
        self.member_type = member_type
        return super(CeDESRegisteredView, self).__call__()
