# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 by GoForWeb.be
#
# GNU General Public License (GPL)
#

from AccessControl import ClassSecurityInfo
from cedes.core.content.common import Ressource
from cedes.core.content.common import ICommon
from plone.app.contenttypes.content import Link
from plone.app.contenttypes.interfaces import ILink
from plone.app.z3cform.widget import LinkFieldWidget
from plone.autoform import directives
from plone.dexterity.schema import DexteritySchemaPolicy
from zope import schema
from zope.interface import implementer


class ISiteInternet(ICommon, ILink):
    """ """

    directives.widget("remoteUrl", LinkFieldWidget)
    remoteUrl = schema.TextLine(
        title="URL",
        required=False, )


@implementer(ISiteInternet)
class SiteInternet(Link, Ressource):
    """ """
    security = ClassSecurityInfo()


class SiteInternetSchemaPolicy(DexteritySchemaPolicy):
    """Schema Policy for SiteInternet."""

    def bases(self, schema_name, tree):
        return (ISiteInternet, )
