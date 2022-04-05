# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 by GoForWeb.be
#
# GNU General Public License (GPL)
#

from AccessControl import ClassSecurityInfo
from cedes.core.config import CEDES_DS_KW_PREFIX
from cedes.core.interfaces import ICeDESLoveThumbsDontYou
from cedes.core.pisa import _get_pdf_file_path
from plone import api
from plone.app.contenttypes.content import Folder
from plone.app.z3cform.widget import RelatedItemsFieldWidget
from plone.autoform import directives
from plone.dexterity.schema import DexteritySchemaPolicy
from plone.supermodel import model
from z3c.relationfield.schema import RelationChoice
from z3c.relationfield.schema import RelationList
from zope import schema
from zope.interface import implementer

import os


class IDossierStructure(model.Schema):
    """ """

    start_numbering_at = schema.Int(
        title='Commencer la numérotation à',
        default=1,
        required=False, )


class IPoint(model.Schema):
    """ """

    directives.widget(
        'cf_resources',
        RelatedItemsFieldWidget,
        pattern_options={
            'basPath': '/dossiers-structures',
            'selectableTypes': ['ArticleGratuit', 'ArticlePayant',
                                'SiteInternet', 'Statistiques', 'Audio',
                                'Video', 'Cederom', 'Bibliographie',
                                'SequenceApprentissage', 'Link']}, )
    cf_resources = RelationList(
        title='Ressources illustrant ce point',
        value_type=RelationChoice(
            vocabulary='plone.app.vocabularies.Catalog',
        ),
        required=False, )


class Base(object):

    security = ClassSecurityInfo()

    security.declarePrivate('get_sub_points')

    def get_sub_points(self):
        """
          returns all the direct points of this Folder
        """
        return self.objectValues()

    security.declarePrivate('get_price')

    def get_price(self, total=False):
        """
          Returns the number of Article Payant contained in this file the current
          member has not already payed
          If total is True, return the total price no matter the member already payed
        """
        ressource_uids = self.get_all_ressource_uids()
        if not total:
            # remove already payed ArticlePayant
            member = api.user.get_current()
            already_payed_uids = [elt[0] for elt in member.get_account_transactions()]
            ressource_uids = set(ressource_uids).difference(set(already_payed_uids))
        return len(self.get_paying_ressources(tuple(ressource_uids)))

    security.declarePrivate('get_paying_ressources')

    def get_paying_ressources(self, uids):
        """
        Returns brains of paying ressources (ArticlePayant)
        """
        catalog = api.portal.get_tool('portal_catalog')
        return catalog(UID=uids)


@implementer(IDossierStructure, ICeDESLoveThumbsDontYou)
class DossierStructure(Folder, Base):
    """Dossier structuré """

    security = ClassSecurityInfo()

    security.declarePrivate('is_dossier_structure')

    def is_dossier_structure(self):
        """
          returns True if this is the file, False if it's a Point
        """
        return True

    security.declarePublic('get_dossier_structure')

    def get_dossier_structure(self):
        """
          Returns the self
        """
        return self

    security.declarePrivate('get_all_ressource_uids')

    def get_all_ressource_uids(self):
        """
          returns Returns the list of all ressources referenced in this file (uid list)
        """
        res = []
        subitems = self.get_sub_points()
        for item in subitems:
            res = res + item.get_all_ressource_uids()
        return res

    def is_pdf_generated(self):
        """ """
        return os.path.exists(_get_pdf_file_path(self))

    def get_container_kw_marker(self):
        """If container (Folder) of this DS use a keyword that begins with CEDES_DS_KW_MARKER,
           we return it, else we return None."""
        container = self.aq_inner.aq_parent
        for kw in container.Subject():
            if kw.startswith(CEDES_DS_KW_PREFIX):
                return kw
        return None


def _compute_ds_subject(resource):
    """Compute DS related kw and add it to resource Subject.
       We recompute every kw because a resource could have been removed but linked
       to other Points using same kw, ..."""
    # get current subject without ds related kw
    subject = [subject for subject in resource.Subject()
               if not subject.startswith(CEDES_DS_KW_PREFIX)]
    # compute ds related kw
    ds_subject = []
    for cr_point in resource.getCr_points():
        ds_subject.append(cr_point.getDossierStructure().get_container_kw_marker())
    # remove duplicates, it is the case if linked to several Point of different
    # DS using same container with ds kw
    ds_subject = list(set(ds_subject))
    # set Subject
    resource.setSubject(subject + ds_subject)
    resource.reindexObject(idxs=['Subject'])


@implementer(IPoint)
class Point(Folder, Base):
    """Un point d'un dossier structuré"""

    security = ClassSecurityInfo()

    security.declarePrivate('is_dossier_structure')

    def is_dossier_structure(self):
        """
          returns True if this is the file, False if it's a Point
        """
        return False

    security.declarePublic('get_dossier_structure')

    def get_dossier_structure(self):
        """
          Returns the DossierStructure of this point (recursive)
        """
        parent = self.getParentNode()
        if parent.is_dossier_structure():
            return parent
        return parent.get_dossier_structure()

    security.declarePrivate('get_all_ressource_uids')

    def get_all_ressource_uids(self):
        """
          Returns the list of all ressources referenced in this Point (uid list)
        """
        res = []
        if self.cf_resources:
            res = res + [ress.to_object.UID() for ress in self.cf_resources]
        subitems = self.get_sub_points()
        for item in subitems:
            res = res + item.get_all_ressource_uids()
        return res

    def get_cf_resources(self, the_objects=False):
        """ """
        if not the_objects:
            return self.cf_resources
        else:
            return [ressource.to_object for ressource in self.cf_resources]

    def setCf_resources(self, value, **kwargs):
        """
          Override mutator to :
          - reindex 'has_cr_points' index on added/removed resources;
          - if folder containing the DS has a keyword that begin with 'dossierstructure-marker-'
            then we will add this keyword to every resources linked to a Point of a DS of this
            Folder and reindex the 'Subject' index for it.
        """
        # XXX to be fixed !!!
        # remove empty values
        value = [v for v in value if v]
        stored = self.getRawCf_resources()
        added_or_removed = list(set(stored).symmetric_difference(set(value)))
        self.getField('cf_resources').set(self, value, **kwargs)
        # now that references are added/removed, we can update has_cr_points
        # and if kw_marker, manage 'Subject'
        catalog = api.portal.get_tool('portal_catalog')
        added_or_removed_objs = [brain.getObject() for brain in catalog(UID=added_or_removed)]
        for resource in added_or_removed_objs:
            _compute_ds_subject(resource)
            resource.reindexObject(idxs=['has_cr_points'])


class DossierStructureSchemaPolicy(DexteritySchemaPolicy):
    """Schema Policy for DossierStructure."""

    def bases(self, schema_name, tree):
        return (IDossierStructure, )


class PointSchemaPolicy(DexteritySchemaPolicy):
    """Schema Policy for Point."""

    def bases(self, schema_name, tree):
        return (IPoint, )
