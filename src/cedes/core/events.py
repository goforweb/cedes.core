# -*- coding: utf-8 -*-

from cedes.core import logger
from cedes.core.interfaces import IThemeFacetedNavigable
from cedes.core.utils import get_modified_attrs
from datetime import datetime
from eea.facetednavigation.interfaces import IHidePloneLeftColumn
from eea.facetednavigation.layout.interfaces import IFacetedLayout
from persistent.list import PersistentList
from persistent.mapping import PersistentMapping
from plone import api
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


def onRessourceModified(obj, event):
    """Called when existing ressource modified."""
    # set a first classification date if empty and a classification is defined
    if not obj.cr_first_classification_date and obj.cr_classification:
        obj.cr_first_classification_date = datetime.now()
    # remove first classification date if no more classification
    elif not obj.cr_classification:
        obj.cr_first_classification_date = None


def onRessourceLiked(obj, event):
    """ """
    obj.reindexObject(idxs=['user_ratings'])


def onRessourceUnliked(obj, event):
    """ """
    obj.reindexObject(idxs=['user_ratings'])


def onPrincipalCreated(event):
    """Register new user into the account_bills and account_transactions PersistentMappings."""
    # create account_bills and account_transactions if it does not exist
    portal = api.portal.get()
    account_bills = getattr(portal, 'account_bills', None)
    if account_bills is None:
        portal.account_bills = PersistentMapping()
        portal.account_transactions = PersistentMapping()
    portal.account_bills[event.object.getId()] = PersistentList()
    portal.account_transactions[event.object.getId()] = PersistentList()


def onPrincipalDeleted(event):
    """ """
    if event.object.getId() in portal.account_bills:
        del portal.account_bills[event.object.getId()]
    if event.object.getId() in portal.account_transactions:
        del portal.account_transactions[event.object.getId()]
