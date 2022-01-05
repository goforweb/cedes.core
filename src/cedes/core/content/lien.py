# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 by GoForWeb.be
#
# GNU General Public License (GPL)
#

from cedes.core.content.ressource import IRessource
from cedes.core.content.ressource import Ressource
from plone.app.contenttypes.content import Link
from plone.app.contenttypes.interfaces import ILink
from plone.app.z3cform.widget import LinkFieldWidget
from plone.autoform import directives
from zope import schema
from zope.interface import implementer


class ILien(IRessource, ILink):
    """ """

    directives.widget("remoteUrl", LinkFieldWidget)
    remoteUrl = schema.TextLine(
        title="URL",
        required=False, )


@implementer(ILien)
class Lien(Link, Ressource):
    """ """
