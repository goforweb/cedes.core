# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 by GoForWeb.be
#
# GNU General Public License (GPL)
#

from AccessControl import ClassSecurityInfo
from cedes.core.content.resource import IResource
from cedes.core.content.resource import Resource
from plone.app.contenttypes.content import Document
from plone.app.contenttypes.interfaces import IDocument
from plone.app.textfield import RichText
from plone.dexterity.schema import DexteritySchemaPolicy
from plone.namedfile.field import NamedBlobFile
from plone.supermodel import model
from zope import schema
from zope.interface import implementer


try:
    from plone.app.dexterity.textindexer.directives import searchable
except ImportError:
    from collective.dexteritytextindexer.directives import searchable


class IBibliographie(IResource, IDocument):
    """ """

    searchable("cr_subtitle")
    cr_subtitle = schema.TextLine(
        title='Sous-titre',
        required=False, )

    searchable("cr_author")
    cr_author = schema.TextLine(
        title='Auteur',
        required=False, )

    cr_reference = schema.TextLine(
        title='Références',
        required=False, )

    model.primary('file')
    file = NamedBlobFile(
        title='Fichier PDF',
        required=False, )

    searchable("text")
    text = RichText(
        title='Description',
        allowed_mime_types=(u"text/html", ),
        required=False, )

    searchable("cr_links")
    cr_links = RichText(
        title='Liens',
        allowed_mime_types=(u"text/html", ),
        required=False, )


@implementer(IBibliographie)
class Bibliographie(Document, Resource):
    """ """
    security = ClassSecurityInfo()

    security.declarePublic('get_colophon_with_author')

    def get_colophon_with_author(self):
        """
          returns the colophon with author
        """
        colophon = ''
        if self.cr_author:
            colophon += self.cr_author
        if self.cr_author and self.cr_reference:
            colophon += ' &mdash; '
        if self.cr_reference:
            colophon += self.cr_reference
        return colophon


class BibliographieSchemaPolicy(DexteritySchemaPolicy):
    """Schema Policy for Bibliographie."""

    def bases(self, schema_name, tree):
        return (IBibliographie, )
