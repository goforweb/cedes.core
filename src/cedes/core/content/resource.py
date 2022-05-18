# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 by GoForWeb.be
#
# GNU General Public License (GPL)
#

from AccessControl import ClassSecurityInfo
from cedes.core.interfaces import ICeDESLoveThumbsDontYou
from cedes.core.config import CEDES_RESOURCE_TYPES
from cedes.core.utils import get_intid
from cedes.core.utils import get_relations
from collective.dexteritytextindexer.directives import searchable
from plone import api
from plone.app.z3cform.widget import RelatedItemsFieldWidget
from plone.autoform import directives
from plone.supermodel import model
from z3c.relationfield.schema import RelationChoice
from z3c.relationfield.schema import RelationList
from zope import schema
from zope.interface import implementer
from z3c.relationfield.relation import RelationValue
from zope.event import notify
from zope.globalrequest import getRequest
from zope.lifecycleevent import ObjectModifiedEvent


class IResource(model.Schema):
    """ """

    searchable("cr_comment")
    cr_comment = schema.Text(
        title='Commentaire',
        required=False, )

    directives.widget(
        'cr_classification',
        RelatedItemsFieldWidget,
        pattern_options={
            'basePath': '/sitecedes/plan',
            'selectableTypes': ['Theme'],
            'mode': 'auto', }, )
    cr_classification = RelationList(
        title='Classification',
        value_type=RelationChoice(
            vocabulary='plone.app.vocabularies.Catalog',
        ),
        required=False,
        default=[], )

    cr_first_classification_date = schema.Date(
        title='Date d\'encodage sur le CeDES (initialisé automatiquement lors '
        'de la première classification)',
        required=False, )

    directives.widget(
        'cr_points',
        RelatedItemsFieldWidget,
        pattern_options={
            'basePath': '/sitecedes/dossiers-structures',
            'selectableTypes': ['Point'], }, )
    cr_points = RelationList(
        title='Points auxquels la resource est liée',
        value_type=RelationChoice(
            vocabulary='plone.app.vocabularies.Catalog',
        ),
        required=False, )

    directives.widget(
        'related_items',
        RelatedItemsFieldWidget,
        pattern_options={
            'basePath': '/sitecedes/ressources',
            'selectableTypes': CEDES_RESOURCE_TYPES, }, )
    related_items = RelationList(
        title='Ressources liées',
        value_type=RelationChoice(
            vocabulary='plone.app.vocabularies.Catalog',
        ),
        required=False, )


@implementer(IResource, ICeDESLoveThumbsDontYou)
class Resource(object):
    """ """

    security = ClassSecurityInfo()

    def get_associated_themes(self, as_uids=True):
        """
          Returns all the associated Themes WITHOUT their parents.
          When p_as_uids=True, returns UID of themes.
        """
        res = [theme.to_object for theme in self.cr_classification
               if theme]
        if as_uids:
            res = [theme.UID() for theme in res]
        return res

    def get_all_associated_themes(self, as_uids=True):
        """
          Returns all the associated Themes AND their parents.
          When p_as_uids=True, returns UID of themes.
        """
        res = []
        associated_themes = self.get_associated_themes(as_uids=False)
        for theme in associated_themes:
            for p in theme.get_themes_path():
                res += [p]
        if as_uids:
            res = [theme.UID() for theme in res]
        return res

    def get_associated_themes_title_and_path(self):
        """
          returns a list of tuples containing all associated Themes
          (Title, TitlePath and path)
        """
        res = []
        portal_url = api.portal.get_tool('portal_url')
        associated_themes = self.get_associated_themes(as_uids=False)
        for theme in associated_themes:
            res.append((theme.Title(), theme.get_title_path(), '/'.join(
                portal_url.getRelativeContentPath(theme))))
        return res

    def get_cr_points(self, the_objects=False):
        """Field "cr_points" stores nothing but will just be used to show back relations."""
        back_relations = get_relations(self, attribute='cf_resources', backrefs=True)
        res = []
        if the_objects:
            res = [back_rel.from_object for back_rel in back_relations]
        else:
            res = [RelationValue(get_intid(back_rel.from_object))
                   for back_rel in back_relations]
        return res

    def set_cr_points(self, values):
        '''Override 'cr_points' mutator so we can manage resource insertion
           into a 'Point' or resource removal from a 'Point'.
           Actually nothing is stored, but we check compared to what we receive in
           p_value and what we have as back references (by calling self.getCr_points)
           and we know where we need to add the resource and where we need to remove it.
           If a resource is already linked to a 'Point', we do nothing.'''
        current_rels = self.get_cr_points()
        current_points = [rel.to_object for rel in current_rels]
        new_points = [rel.to_object for rel in values]

        # manage removal
        # collect Point no more selected
        removed_points = [point for point in current_points if point not in new_points]
        for point in removed_points:
            new_cf_resources = [rel for rel in point.cf_resources
                                if rel.to_object.UID() != self.UID()]
            point.cf_resources = new_cf_resources
            # notify modified so catalog is updated
            notify(ObjectModifiedEvent(point))

        # manage addition
        added_points = [point for point in new_points if point not in current_points]
        for point in added_points:
            # resource is insterted at the beginning of Point cf_resources
            new_cf_resources = [RelationValue(get_intid(self))] + point.cf_resources
            point.cf_resources = new_cf_resources
            # notify modified so catalog is updated
            notify(ObjectModifiedEvent(point))

        # manage DS Subject
        # DS related kw Subject are added automatically
        # when editing Points from resource, make sure it is not in request.form.Subject
        # or when removing from a Point using DS Subject, the kw is reapplied on form save...
        # mark in request that we need to remove it in the onResourceModified as correct Subject
        # was recomputed in Point.set_cf_resources
        req = getRequest()
        req.set('computed_Subject', self.Subject())

        # we store nothing
        return

    # accessor/mutator for field "cr_points"
    cr_points = property(get_cr_points, set_cr_points)
