# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 by GoForWeb.be
#
# GNU General Public License (GPL)
#

from cedes.core import logger
from cedes.core.content.resource import IResource
from cedes.core.interfaces import ICeDESLoveThumbsDontYou
from cedes.core.utils import normalize_data
from cioppino.twothumbs.rate import yays
from plone.app.textfield.interfaces import IRichText
from plone.indexer import indexer
from z3c.form.interfaces import IWidget
from zope.annotation import IAnnotations
from zope.component import adapter
from zope.component import adapts
from zope.interface import implementer


try:
    from plone.app.dexterity.textindexer.converters import DexterityRichTextIndexFieldConverter
    from plone.app.dexterity.textindexer.interfaces import IDexterityTextIndexFieldConverter
    from plone.app.dexterity.textindexer.interfaces import IDynamicTextIndexExtender
except ImportError:
    from collective.dexteritytextindexer.converters import DexterityRichTextIndexFieldConverter
    from collective.dexteritytextindexer.interfaces import IDexterityTextIndexFieldConverter
    from collective.dexteritytextindexer.interfaces import IDynamicTextIndexExtender


@indexer(ICeDESLoveThumbsDontYou)
def user_ratings(obj, **kw):
    """Index users that loved a resource."""
    ann = IAnnotations(obj)
    return list(ann.get(yays, {}))


@indexer(IResource)
def has_cr_points(resource):
    """Is resource linked to some Points?"""
    cr_points = resource.cr_points
    # remove 'None' from the cr_points
    return bool([point for point in cr_points if point])


@indexer(IResource)
def associated_theme_uids(resource):
    """
    """
    return resource.get_associated_themes(as_uids=True)


@indexer(IResource)
def all_associated_theme_uids(resource):
    """
    """
    return resource.get_all_associated_themes(as_uids=True)


@indexer(IResource)
def associated_themes_title_and_path(resource):
    """
    """
    return resource.get_associated_themes_title_and_path()


@indexer(IResource)
def cr_date_index(resource):
    """
    """
    return resource.cr_date


@indexer(IResource)
def cr_first_classification_date_index(resource):
    """
    """
    return resource.cr_first_classification_date


@indexer(IResource)
def title_path(resource):
    """
    """
    return resource.get_title_path()


@indexer(IResource)
def colophon_with_author(resource):
    """
    """
    return resource.get_colophon_with_author()


@implementer(IDexterityTextIndexFieldConverter)
@adapter(IResource, IRichText, IWidget)
class ResourceRichTextIndexFieldConverter(DexterityRichTextIndexFieldConverter):
    """ """

    def convert(self):
        """After RichText has been converted to text/plain,
           normalize the result."""
        data = super(ResourceRichTextIndexFieldConverter, self).convert()
        try:
            data = normalize_data(data)
        except Exception:
            logger.error(
                "Object at '%s' could not be reindexed correctly!" % ' '.join(
                    self.context.getPhysicalPath()))
        return data


@implementer(IDynamicTextIndexExtender)
class ResourceSearchableTextExtender(object):

    adapts(IResource)

    def __init__(self, context):
        self.context = context

    def __call__(self):
        """Include associated themes title and subjects."""
        res = []
        for theme in self.context.get_associated_themes(as_uids=False):
            res.append(theme.Title())
            res += list(theme.Subject())
        res = ' '.join(res)
        return res
