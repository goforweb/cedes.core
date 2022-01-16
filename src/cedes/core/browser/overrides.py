# -*- coding: utf-8 -*-

from plone.app.contenttypes.browser.folder import FolderView


class CedesFolderView(FolderView):
    """ """

    @property
    def no_items_message(self):
        """Do not display the message 'There is no element in this folder.'"""
        import ipdb; ipdb.set_trace()
        return ''
