# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 by GoForWeb.be
#
# GNU General Public License (GPL)
#

from cioppino.twothumbs.interfaces import ILoveThumbsDontYou
from eea.facetednavigation.interfaces import IFacetedNavigable
from zope.publisher.interfaces.browser import IDefaultBrowserLayer
from zope.interface import Interface
from plone.dexterity.interfaces import IDexterityContent


class IThemeFacetedNavigable(IFacetedNavigable):
    """Theme faceted navigable inteface"""


class ICedesCoreLayer(IDefaultBrowserLayer):
    """ """


class ICeDESLoveThumbsDontYou(ILoveThumbsDontYou):
    """ """


class IRessource(IDexterityContent):
    """Ressource marker interface"""
