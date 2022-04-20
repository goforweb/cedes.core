# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 by GoForWeb.be
#
# GNU General Public License (GPL)
#

from AccessControl import ClassSecurityInfo
from cedes.core.interfaces import ICeDESLoveThumbsDontYou
from cedes.core.utils import get_intid
from cedes.core.utils import get_relations
from collective.dexteritytextindexer.directives import searchable
from datetime import datetime
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
from zope.lifecycleevent import ObjectModifiedEvent


class IRessource(model.Schema):
    """ """

    searchable("cr_comment")
    cr_comment = schema.Text(
        title='Commentaire',
        required=False, )

    directives.widget(
        'cr_classification',
        RelatedItemsFieldWidget,
        pattern_options={
            'basPath': '/plan',
            'selectableTypes': ['Theme'],
            'mode': 'auto', }, )
    cr_classification = RelationList(
        title='Classification',
        value_type=RelationChoice(
            vocabulary='plone.app.vocabularies.Catalog',
        ),
        required=False,
        default=[], )

    cr_first_classification_date = schema.Datetime(
        title='Date d\'encodage sur le CeDES (initialisé automatiquement lors '
        'de la première classification)',
        required=False, )

    directives.widget(
        'cr_points',
        RelatedItemsFieldWidget,
        pattern_options={
            'basPath': '/dossiers-structures',
            'selectableTypes': ['Point'], }, )

    cr_points = RelationList(
        title='Points auxquels la ressource est liée',
        value_type=RelationChoice(
            vocabulary='plone.app.vocabularies.Catalog',
        ),
        required=False, )

    directives.widget(
        'related_items',
        RelatedItemsFieldWidget,
        pattern_options={}, )

    related_items = RelationList(
        title='Ressources liées',
        value_type=RelationChoice(
            vocabulary='plone.app.vocabularies.Catalog',
        ),
        required=False, )


@implementer(IRessource, ICeDESLoveThumbsDontYou)
class Ressource(object):
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

    def setCr_classification(self, value, **kwargs):
        """
          When associated Theme changes, adds Title and Keywords to this ressource
        """
        # XXX to be fixed
        # if old value is empty, we init the cr_first_classification_date field
        old_value = self.getField('cr_classification').getAccessor(self)()
        if not old_value:
            self.setCr_first_classification_date(datetime.now())
        # remove cr_first_classification_date if removing classification
        if not value or value == ['']:
            self.setCr_first_classification_date(None)
        self.getField('cr_classification').set(self, value, **kwargs)

    security.declarePublic('getCr_points_base_query')

    def getCr_points_base_query(self):
        """
          Hack for sorting first level on 'getObjPositionInParent' or first shown elements are not sorted
        """
        # XXX to be fixed
        dict = {}
        dict['sort_on'] = 'getObjPositionInParent'
        return dict

    security.declarePublic('getCr_classification_base_query')

    def getCr_classification_base_query(self):
        """
          Hack for sorting first level on 'getObjPositionInParent' or first shown elements are not sorted
        """
        # XXX to be fixed
        dict = {}
        dict['sort_on'] = 'getObjPositionInParent'
        return dict

    def get_cr_points(self):
        """Field "cr_points" stores nothing but will just be used to show back relations."""
        return [RelationValue(get_intid(rel.from_object))
                for rel in get_relations(self, attribute='cf_resources', backrefs=True)]

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

        # we store nothing
        return

    cr_points = property(get_cr_points, set_cr_points)

    def getCr_points(self, **kwargs):
        """Override get() methods, we do not store anything in this field,
           but we show back references of 'Point' that are referencing this element."""
        # XXX to be fixed
        # remove empty refs, make sure we have no None
        refs = [ref for ref in self.getBRefs(relationship='cf_resources') if ref is not None]
        return refs

    def getRawCr_points(self, **kwargs):
        """Override getRaw() methods, we do not store anything in this field,
           but we show back references of 'Point' that are referencing this element."""
        # XXX to be fixed
        refs = [ref.UID() for ref in self.getBRefs(relationship='cf_resources') if ref is not None]
        return refs

    security.declareProtected('Modify portal content', 'setCr_points')

    def setCr_points(self, value, **kwargs):
        '''Override 'cr_points' mutator so we can manage resource insertion
           into a 'Point' or resource removal from a 'Point'.
           Actually nothing is stored, but we check compared to what we receive in
           p_value and what we have as back references (by calling self.getCr_points)
           and we know where we need to add the resource and where we need to remove it.
           If a resource is already linked to a 'Point', we do nothing.'''
        # XXX to be fixed
        current_ref_uids = self.getRawCr_points()
        catalog = api.portal.get_tool('portal_catalog')

        # manage removal
        for to_remove in current_ref_uids:
            point = catalog(UID=to_remove)[0].getObject()
            if self.UID() in point.getRawCf_resources():
                resource_uids = point.getRawCf_resources()
                resource_uids.remove(self.UID())
                point.setCf_resources(resource_uids)
                point._p_changed = True

        # manage addition
        for to_add in value:
            if not to_add:
                continue
            point = catalog(UID=to_add)[0].getObject()
            if not self.UID() in point.getRawCf_resources():
                point.setCf_resources([self.UID()] + point.getRawCf_resources())
                point._p_changed = True

        # manage DS Subject
        # DS related kw Subject are added automatically
        # when editing Points from resource, make sure it is not in request.form.Subject
        # or when removing from a Point using DS Subject, the kw is reapplied on form save...
        subject_existing_keywords = self.REQUEST.form.get('subject_existing_keywords', None)
        if subject_existing_keywords is not None:
            self.REQUEST.form['subject_existing_keywords'] = list(self.Subject())

        # force set nothing
        self.getField('cr_points').set(self, [], **kwargs)
        self._p_changed = True

    security.declarePublic('getRelatedItems_base_query')

    def getRelatedItems_base_query(self):
        """
          Hack for sorting first level on 'getObjPositionInParent' or first shown elements are not sorted
        """
        # XXX to be fixed
        dict = {}
        dict['sort_on'] = 'getObjPositionInParent'
        return dict
