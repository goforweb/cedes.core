# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 by GoForWeb.be
#
# GNU General Public License (GPL)
#

from AccessControl import ClassSecurityInfo
from cedes.core.content.resource import IResource
from cedes.core.content.resource import Resource
from collective.dexteritytextindexer.directives import searchable
from plone.app.contenttypes.content import Document
from plone.app.contenttypes.interfaces import IDocument
from plone.app.textfield import RichText
from plone.dexterity.schema import DexteritySchemaPolicy
from plone.namedfile.field import NamedBlobFile
from plone.supermodel import model
from zope import schema
from zope.interface import implementer


class ISequenceApprentissage(IResource, IDocument):
    """ """

    cr_reference = schema.TextLine(
        title='Références',
        required=False, )

    model.primary('cr_file')
    cr_file = NamedBlobFile(
        title='Fichier PDF',
        required=False, )

    searchable("text")
    text = RichText(
        title="Contenus",
        allowed_mime_types=(u"text/html", ),
        required=False, )


@implementer(ISequenceApprentissage)
class SequenceApprentissage(Document, Resource):
    """ """
    security = ClassSecurityInfo()

    security.declarePublic('get_colophon_with_author')

    def get_colophon_with_author(self):
        """
          returns the colophon with author
        """
        colophon = ''
        if self.cr_reference:
            colophon += self.cr_reference
        return colophon


class SequenceApprentissageSchemaPolicy(DexteritySchemaPolicy):
    """Schema Policy for SequenceApprentissage."""

    def bases(self, schema_name, tree):
        return (ISequenceApprentissage, )
