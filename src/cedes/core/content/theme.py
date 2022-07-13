# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 by GoForWeb.be
#
# GNU General Public License (GPL)
#

from AccessControl import ClassSecurityInfo
from cedes.core.config import CEDES_RESOURCE_TYPES
from cedes.core.utils import get_intid
from plone import api
from plone.app.z3cform.widget import RelatedItemsFieldWidget
from plone.autoform import directives
from plone.dexterity.content import Container
from plone.dexterity.schema import DexteritySchemaPolicy
from plone.supermodel import model
from z3c.relationfield.relation import RelationValue
from z3c.relationfield.schema import RelationChoice
from z3c.relationfield.schema import RelationList
from zope.event import notify
from zope.interface import implementer
from zope.lifecycleevent import ObjectModifiedEvent


class ITheme(model.Schema):
    """ """

    directives.widget(
        'cc_related',
        RelatedItemsFieldWidget,
        pattern_options={
            'basePath': '/sitecedes/plan',
            'selectableTypes': ['Theme'],
        }, )
    cc_related = RelationList(
        title='Voir aussi',
        value_type=RelationChoice(
            vocabulary='plone.app.vocabularies.Catalog',
        ),
        required=False, )


@implementer(ITheme)
class Theme(Container):
    """ """

    security = ClassSecurityInfo()

    security.declarePublic('get_title_path')

    def get_title_path(self, separator="->"):
        """
          Build the title path like physical path (used for displaying the breadcrumbs)
        """
        separator = ' ' + separator + ' '
        return separator.join([p.Title() for p in self.get_themes_path(include_root=False)])

    security.declarePublic('is_root')

    def is_root(self):
        """
          returns True if this object is the root of the classification scheme
        """
        return self.portal_type == "PlanClassement"

    security.declarePublic('get_root_theme')

    def get_root_theme(self):
        """
          Returns the root Theme of this theme (recursive)
        """
        parent = self.aq_inner.aq_parent
        if parent.is_root():
            return parent
        return parent.get_root_theme()

    security.declarePublic('get_cc_related')

    def get_cc_related(self, the_objects=False):
        """ """
        if not the_objects:
            # cc_related may not exist when creating new element
            return self.__dict__.get('cc_related', [])
        else:
            return [theme.to_object for theme in self.cc_related]

    def set_cc_related(self, values, **kwargs):
        """
          Override mutator to be able to manage BiReference.
        """
        new = [rel.to_object for rel in values]
        stored = self.get_cc_related(True)
        added = [theme for theme in new if theme not in stored]
        removed = [theme for theme in stored if theme not in new]

        # store value and update relations because we need it now
        self.__dict__['cc_related'] = values

        # update references of removed elements
        uid = self.UID()
        for theme in removed:
            new_cc_related = [rel for rel in theme.cc_related
                              if rel.to_object.UID() != uid]
            theme.__dict__['cc_related'] = new_cc_related
            # notify modified so catalog is updated
            notify(ObjectModifiedEvent(theme))

        # update references of added elements
        for theme in added:
            new_cc_related = theme.cc_related + [RelationValue(get_intid(self))]
            theme.__dict__['cc_related'] = new_cc_related
            # notify modified so catalog is updated
            notify(ObjectModifiedEvent(theme))

    # accessor/mutator for field "cf_resources"
    cc_related = property(get_cc_related, set_cc_related)

    security.declarePublic('get_associated_resources')

    def get_associated_resources(self, sorted=True, summary=False):
        """
          List of resources classified under this theme
          @param sorted if True, return resources sorted by order of importance
          @param summary if True, only return resource type details as dictionary (sorted must be True)
          @return List of resources classified under this theme
        """
        catalog = api.portal.get_tool('portal_catalog')
        res = catalog(portal_type=CEDES_RESOURCE_TYPES, associated_theme_uids=self.UID())

        if not sorted:
            return res
        sorting_dic = {'ArticlePayant': 0,
                       'ArticleGratuit': 0,
                       'SiteInternet': 0,
                       'SequenceApprentissage': 0,
                       'Statistiques': 0,
                       'Audio': 0,
                       'Video': 0,
                       'Cederom': 0,
                       'Bibliographie': 0}
        res_list = []
        for item in res:
            if not item:
                continue
            sorting_dic[item.portal_type] = sorting_dic[item.portal_type] + 1
            res_list.append(item)
        if summary:
            return sorting_dic

        res_list.sort()
        return res_list

    security.declarePublic('get_nb_associated_resources')

    def get_nb_associated_resources(self):
        """
          returns The number of associated resources
        """
        res = self.get_associated_resources(sorted=False)
        return len(res)

    def get_themes_path(self, include_root=True, include_self=True):
        """
          Recursivly builds a sequence of Theme objects along the path to this theme
          returns list of Themes composing the path to this one
        """
        try:
            up_to_here = self.aq_parent.get_themes_path(include_root)
            if include_self:
                return up_to_here + [self]
            else:
                return up_to_here
        except AttributeError:
            if include_self:
                return [self]
            else:
                return []

    security.declarePublic('get_short_title')

    def get_short_title(self, short_length=20):
        """
          returns short title of this subdivision (used for nice display of javacript tree)
          param short_length number of caracters to keep, truncate the rest
        """
        title = self.Title().strip()
        if len(title) > short_length:
            title = title[:short_length] + '...'
        return title.encode('UTF-8')


class ThemeSchemaPolicy(DexteritySchemaPolicy):
    """Schema Policy for Theme"""

    def bases(self, schema_name, tree):
        return (ITheme, )
