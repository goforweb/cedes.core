# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 by GoForWeb.be
#
# GNU General Public License (GPL)
#

from AccessControl import ClassSecurityInfo
from cedes.core.content.lien import ILien
from cedes.core.content.lien import Lien
from plone.dexterity.schema import DexteritySchemaPolicy
from zope.interface import implementer


class IVideo(ILien):
    """ """


@implementer(IVideo)
class Video(Lien):
    """ """
    security = ClassSecurityInfo()


class VideoSchemaPolicy(DexteritySchemaPolicy):
    """Schema Policy for Video."""

    def bases(self, schema_name, tree):
        return (IVideo, )
