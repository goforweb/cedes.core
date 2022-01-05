# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 by GoForWeb.be
#
# GNU General Public License (GPL)
#

from AccessControl import ClassSecurityInfo
from cedes.core.content.common import ICommon
from cedes.core.content.common import Ressource
from plone.app.contenttypes.content import Link
from plone.app.contenttypes.interfaces import ILink
from plone.app.z3cform.widget import LinkFieldWidget
from plone.autoform import directives
from zope import schema
from zope.interface import implementer


class ILien(ICommon, ILink):
    """ """

    directives.widget("remoteUrl", LinkFieldWidget)
    remoteUrl = schema.TextLine(
        title="URL",
        required=False, )


@implementer(ILien)
class Lien(Link, Ressource):
    """ """
