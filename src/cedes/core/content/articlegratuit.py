# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 by GoForWeb.be
#
# GNU General Public License (GPL)
#

from AccessControl import ClassSecurityInfo
from zope import schema
from collective.dexteritytextindexer.directives import searchable
from cedes.core.content.common import ICommon
from cedes.core.content.common import Article
from plone.app.textfield import RichText
from zope.interface import implementer
from plone.app.contenttypes.interfaces import IFile
from plone.app.contenttypes.content import File


class IArticleGratuit(ICommon, IFile):
    """ """

    cr_date = schema.Datetime(
        title='Date de parution',
        required=False, )

    searchable("cr_author")
    cr_author = schema.TextLine(
        title='Auteur', )

    searchable("cr_periodical")
    cr_periodical = schema.TextLine(
        title='Périodique', )

    cr_periodical_number = schema.TextLine(
        title='Numéro du périodique ou date de l\'article', )

    cr_periodical_pp = schema.TextLine(
        title='Numéro de page dans le périodique', )

    cr_words_nb = schema.TextLine(
        title='Nombre de mots', )

    searchable("cr_html_preview")
    cr_html_preview = RichText(
        title='Aperçu',
        default_mime_type='text/plain',
        allowed_mime_types=("text/plain", ),
        output_mime_type='text/x-html-safe',
        required=False)


@implementer(IArticleGratuit)
class ArticleGratuit(File, Article):
    """ """

    security = ClassSecurityInfo()

    def getIcon(self, relative_to_portal=0):
        """
          override the default method to avoid application based icon such as pdf icon to appear
        """
        return super(File, self).getIcon(relative_to_portal)

    security.declarePublic('get_colophon')

    def get_colophon(self):
        """
          Returns the colophon of a resource
        """
        colophon = ''
        if self.cr_periodical:
            colophon += self.cr_periodical
        if self.cr_periodical_number:
            colophon += ', n&deg; ' + self.getCr_periodical_number()
        if self.cr_periodical_pp:
            colophon += ', p. ' + self.cr_periodical_pp
        if self.cr_words_nb:
            colophon += ', ' + self.cr_words_nb + ' mots'
        return colophon

    security.declarePublic('get_colophon_with_author')

    def get_colophon_with_author(self):
        """
          Returns the colophon with informations about the author
        """
        colophon = ''
        if self.cr_author:
            colophon += self.cr_author + ' &mdash; '
        colophon += self.get_colophon()
        return colophon
