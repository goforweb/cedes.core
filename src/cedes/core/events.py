# -*- coding: utf-8 -*-

from cedes.core import logger
from cedes.core.interfaces import IThemeFacetedNavigable
from cedes.core.utils import get_modified_attrs
from eea.facetednavigation.interfaces import IHidePloneLeftColumn
from eea.facetednavigation.layout.interfaces import IFacetedLayout
from persistent.list import PersistentList
from zope.annotation import IAnnotations
from zope.interface import alsoProvides
from zope.interface import noLongerProvides


def onThemeAdded(theme, event):
    """Called when new theme added."""
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


def onThemeModified(theme, event):
    """Called when existing theme modified."""
    mod_attrs = get_modified_attrs(event)
    if 'title' in mod_attrs or 'IDublinCore.subjects' in mod_attrs:
        # reindex associated ressources as theme title and description
        # is indexed in ressources SearchableText
        associated = theme.get_associated_resources(sorted=False)
        for item in associated:
            item = item.getObject()
            item.reindexObject(idxs=['SearchableText'])


def onRessourceLiked(obj, event):
    """ """
    obj.reindexObject(idxs=['user_ratings'])


def onRessourceUnliked(obj, event):
    """ """
    obj.reindexObject(idxs=['user_ratings'])
