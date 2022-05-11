# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 by GoForWeb.be
#
# GNU General Public License (GPL)
#

from cedes.core.config import CEDES_PLAN_ROOT
from cedes.core.config import CEDES_RESOURCE_TYPES
from plone import api
from plone.app.contenttypes.content import Document
from plone.app.contenttypes.interfaces import IDocument
from plone.app.textfield import RichText as RichTextField
from plone.app.z3cform.widget import RichTextFieldWidget
from plone.autoform import directives
from plone.batching import Batch
from plone.dexterity.schema import DexteritySchemaPolicy
from plone.supermodel import model
from zope import schema
from zope.interface import implementer


class IEmailContent(IDocument):
    """ """

    newsletter_from = schema.Date(
        title='Newsletter: date de début de sélection',
        description="Laissez vide s'il ne s'agit pas d'une newsletter",
        required=False, )

    newsletter_to = schema.Date(
        title='Newsletter: date de fin de sélection',
        description="Laissez vide s'il ne s'agit pas d'une newsletter",
        required=False, )

    send_to_everybody = schema.Bool(
        title='Envoyer à tout le monde (même les membres qui ont décochés la case '
              '\"Recevoir notre newsletter?\")?',
        required=False,
        default=False, )

    directives.widget('text', RichTextFieldWidget)
    model.primary('text')
    text = RichTextField(
        title='Texte envoyé par e-mail',
        description='Les termes [header], [footer] et [newsletter] peuvent être utilisés '
                    'dans le texte et seront remplacés automatiquement',
        required=False, )


@implementer(IEmailContent)
class EmailContent(Document):
    """ """

    def get_newsletter_content(self):
        """If we have a newsletter_from and a newsletter_to then we can get newsletter content."""
        res = []
        if self.newsletter_from and self.newsletter_to:
            # create list of UIDS of plan first levels
            portal = api.portal.get()
            plan_root = getattr(portal, CEDES_PLAN_ROOT)
            themes = []
            wfTool = api.portal.get_tool("portal_workflow")
            for theme in plan_root.objectValues():
                if wfTool.getInfoFor(theme, 'review_state') == 'published':
                    themes.append(theme)

            # keep search on brains
            i = 0
            catalog = api.portal.get_tool('portal_catalog')
            for theme in themes:
                brains = catalog(portal_type=CEDES_RESOURCE_TYPES,
                                 all_associated_theme_uids=theme.UID(),
                                 cr_first_classification_date_index={
                                     'query': [self.newsletter_from, self.newsletter_to],
                                     'range': 'min:max', },
                                 sort_on='cr_first_classification_date_index')
                if brains:
                    res.append([])
                    res[i].append(theme)
                    batch = Batch(brains, size=10000, orphan=1)
                    res[i].append(batch)
                    i = i + 1

        return res


class EmailContentSchemaPolicy(DexteritySchemaPolicy):
    """Schema Policy for EmailContent."""

    def bases(self, schema_name, tree):
        return (IEmailContent, )
