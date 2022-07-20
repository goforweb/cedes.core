# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 by GoForWeb.be
#
# GNU General Public License (GPL)
#

from cedes.core.content.resource import IResource
from cedes.core.content.resource import Resource
from plone.app.contenttypes.content import Link
from plone.app.contenttypes.interfaces import ILink
from plone.app.z3cform.widget import LinkFieldWidget
from plone.autoform import directives
from zope import schema
from zope.interface import implementer


class ILien(IResource, ILink):
    """ """

    directives.widget("remoteUrl", LinkFieldWidget)
    directives.order_before(remoteUrl='cr_comment')
    remoteUrl = schema.TextLine(
        title="URL",
        required=True, )


@implementer(ILien)
class Lien(Link, Resource):
    """ """
