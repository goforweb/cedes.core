# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 by GoForWeb.be
#
# GNU General Public License (GPL)
#

from AccessControl import ClassSecurityInfo
from cedes.core.content.article import Article
from cedes.core.content.article import IArticle
from plone.dexterity.schema import DexteritySchemaPolicy
from plone.supermodel import model
from zope import schema
from zope.interface import implementer


class IArticleGratuit(IArticle):
    """ """


@implementer(IArticleGratuit)
class ArticleGratuit(Article):
    """ """
    security = ClassSecurityInfo()

    security.declarePublic('get_colophon')

    def get_colophon(self):
        """
          returns the colophon but NOT the cr_date that is used for search on ArticleGratuit.
        """
        return super(ArticleGratuit, self).get_colophon(include_cr_date=False)


class ArticleGratuitSchemaPolicy(DexteritySchemaPolicy):
    """Schema Policy for ArticleGratuit."""

    def bases(self, schema_name, tree):
        return (IArticleGratuit, )
