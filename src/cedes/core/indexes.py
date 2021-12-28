# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 by GoForWeb.be
#
# GNU General Public License (GPL)
#

from cedes.core import logger
from cedes.core.interfaces import ICeDESLoveThumbsDontYou
from cedes.core.interfaces import IRessource
from cedes.core.utils import normalize_data
from cioppino.twothumbs.rate import yays
from collective.dexteritytextindexer.converters import DexterityRichTextIndexFieldConverter
from collective.dexteritytextindexer.interfaces import IDexterityTextIndexFieldConverter
from collective.dexteritytextindexer.interfaces import IDynamicTextIndexExtender
from plone.app.textfield.interfaces import IRichText
from plone.indexer import indexer
from z3c.form.interfaces import IWidget
from zope.annotation import IAnnotations
from zope.component import adapter
from zope.component import adapts
from zope.interface import implementer


@indexer(ICeDESLoveThumbsDontYou)
def user_ratings(obj, **kw):
    """Index users that loved a ressource."""
    ann = IAnnotations(obj)
    return list(ann.get(yays, {}))


@indexer(IRessource)
def has_cr_points(ressource):
    """Is ressource linked to some Points?"""
    cr_points = ressource.cr_points
    # remove 'None' from the cr_points
    return bool([point for point in cr_points if point])


@indexer(IRessource)
def associated_theme_uids(ressource):
    """
    """
    return ressource.get_associated_themes(as_uids=True)


@indexer(IRessource)
def all_associated_theme_uids(ressource):
    """
    """
    return ressource.get_all_associated_themes(as_uids=True)


@indexer(IRessource)
def associated_themes_title_and_path(ressource):
    """
    """
    return ressource.get_associated_themes_title_and_path()


@indexer(IRessource)
def cr_date_index(ressource):
    """
    """
    return ressource.cr_date


@indexer(IRessource)
def cr_first_classification_date_index(ressource):
    """
    """
    return ressource.cr_first_classification_date


@indexer(IRessource)
def title_path(ressource):
    """
    """
    return ressource.get_title_path()


@implementer(IDexterityTextIndexFieldConverter)
@adapter(IRessource, IRichText, IWidget)
class RessourceRichTextIndexFieldConverter(DexterityRichTextIndexFieldConverter):
    """ """

    def convert(self):
        """After RichText has been converted to text/plain,
           normalize the result."""
        data = super(RessourceRichTextIndexFieldConverter, self).convert()
        try:
            data = normalize_data(data)
        except Exception:
            logger.error(
                "Object at '%s' could not be reindexed correctly!" % ' '.join(
                    self.context.getPhysicalPath()))
        return data


@implementer(IDynamicTextIndexExtender)
class RessourceSearchableTextExtender(object):

    adapts(IRessource)

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
