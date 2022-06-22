# -*- coding: utf-8 -*-

from plone import api


def post_handler(context):
    """Post install handler."""
    portal_repository = api.portal.get_tool('portal_repository')
    portal_repository.setVersionableContentTypes([])
