# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 by GoForWeb.be
#
# GNU General Public License (GPL)
#

from cioppino.twothumbs.interfaces import ILoveThumbsDontYou
from eea.facetednavigation.interfaces import IFacetedNavigable
from zope.publisher.interfaces.browser import IDefaultBrowserLayer


class IThemeFacetedNavigable(IFacetedNavigable):
    """Theme faceted navigable inteface"""


class ICedesCoreLayer(IDefaultBrowserLayer):
    """ """


class ICeDESLoveThumbsDontYou(ILoveThumbsDontYou):
    """ """
