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


class IAudio(ILien):
    """ """


@implementer(IAudio)
class Audio(Lien):
    """ """
    security = ClassSecurityInfo()


class AudioSchemaPolicy(DexteritySchemaPolicy):
    """Schema Policy for Audio."""

    def bases(self, schema_name, tree):
        return (IAudio, )
