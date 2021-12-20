# -*- coding: utf-8 -*-

from eea.facetednavigation.layout.interfaces import IFacetedLayout
from eea.facetednavigation.interfaces import IHidePloneLeftColumn
from persistent.list import PersistentList
from cedes.core.interfaces import IThemeFacetedNavigable
from cedes.core import logger
from zope.annotation import IAnnotations
from zope.interface import noLongerProvides
from zope.interface import alsoProvides


def onThemeAdded(theme, event):
    ''' '''
    # enable faceted navigation and configure it
    theme.unrestrictedTraverse('@@faceted_subtyper').enable()
    IFacetedLayout(theme).update_layout('faceted-theme-view')
    # show the left portlets
    if IHidePloneLeftColumn.providedBy(theme):
        noLongerProvides(theme, IHidePloneLeftColumn)
    # remove every criteria as we use criteria stored on PlanClassement
    annotations = IAnnotations(theme)
    annotations['FacetedCriteria'] = PersistentList()
    alsoProvides(theme, IThemeFacetedNavigable)
    logger.info('Faceted navigation enabled for {0}'.format(
        '/'.join(theme.getPhysicalPath())))


def onRessourceLiked(obj, event):
    """ """
    obj.reindexObject(idxs=['user_ratings'])


def onRessourceUnliked(obj, event):
    """ """
    obj.reindexObject(idxs=['user_ratings'])
