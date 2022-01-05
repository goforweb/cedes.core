# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 by GoForWeb.be
#
# GNU General Public License (GPL)
#

from AccessControl import ClassSecurityInfo
from cedes.core.content.ressource import IRessource
from cedes.core.content.ressource import Ressource
from collective.dexteritytextindexer.directives import searchable
from plone.app.contenttypes.content import File
from plone.app.contenttypes.interfaces import IFile
from plone.app.textfield import RichText
from plone.namedfile.field import NamedBlobFile
from plone.supermodel import model
from zope import schema


class IArticle(IRessource, IFile):
    """ """

    cr_date = schema.Datetime(
        title='Date de parution',
        required=False, )

    searchable("cr_author")
    cr_author = schema.TextLine(
        title='Auteur',
        required=False, )

    searchable("cr_periodical")
    cr_periodical = schema.TextLine(
        title='Périodique',
        required=False, )

    cr_periodical_number = schema.TextLine(
        title='Numéro du périodique ou date de l\'article',
        required=False, )

    cr_periodical_pp = schema.TextLine(
        title='Numéro de page dans le périodique',
        required=False, )

    cr_words_nb = schema.TextLine(
        title='Nombre de mots',
        required=False, )

    model.primary('file')
    file = NamedBlobFile(
        title='Fichier',
        required=False, )

    searchable("cr_html_preview")
    cr_html_preview = RichText(
        title='Aperçu',
        allowed_mime_types=(u"text/html", ),
        required=False, )


class Article(File, Ressource):

    security = ClassSecurityInfo()

    def getIcon(self, relative_to_portal=0):
        """
          override the default method to avoid application based icon such as pdf icon to appear
        """
        return super(File, self).getIcon(relative_to_portal)

    security.declarePublic('get_colophon')

    def get_colophon(self, include_cr_date=True):
        """
          returns the colophon: periodical, date, periodical number, pp, nb of words
        """
        colophon = ''
        if self.cr_periodical:
            colophon += self.cr_periodical
        if include_cr_date:
            if self.cr_periodical and self.cr_date:
                colophon += ', '
            if self.cr_date:
                colophon += self.toLocalizedTime(self.cr_date)
        if self.cr_periodical_number:
            colophon += ', n&deg; ' + self.cr_periodical_number
        if self.cr_periodical_pp:
            colophon += ', p. ' + self.cr_periodical_pp
        if self.cr_words_nb:
            colophon += ', ' + self.cr_words_nb + u' mots'
        return colophon

    security.declarePublic('get_colophon_with_author')

    def get_colophon_with_author(self):
        """
          returns the author and colophon
        """
        colophon = ''
        if self.cr_author:
            colophon += self.cr_author + ' &mdash; '
        colophon += self.get_colophon()
        return colophon
