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
from zope.interface import implementer


class IArticlePayant(IArticle):
    """ """


@implementer(IArticlePayant)
class ArticlePayant(Article):
    """ """
    security = ClassSecurityInfo()


class ArticlePayantSchemaPolicy(DexteritySchemaPolicy):
    """Schema Policy for ArticlePayant."""

    def bases(self, schema_name, tree):
        return (IArticlePayant, )
