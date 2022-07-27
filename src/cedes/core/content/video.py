# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 by GoForWeb.be
#
# GNU General Public License (GPL)
#

from AccessControl import ClassSecurityInfo
from cedes.core.content.lien import ILien
from cedes.core.content.lien import Lien
from plone.app.textfield import RichText as RichTextField
from plone.autoform import directives
from plone.dexterity.schema import DexteritySchemaPolicy
from z3c.form.browser.textarea import TextAreaFieldWidget
from zope.interface import implementer


class IVideo(ILien):
    """ """

    directives.widget('cr_preview', TextAreaFieldWidget)
    directives.order_before(cr_preview='remoteUrl')
    cr_preview = RichTextField(
        title='Aperçu',
        description='Code HTML intégration vidéo',
        required=False, )


@implementer(IVideo)
class Video(Lien):
    """ """
    security = ClassSecurityInfo()


class VideoSchemaPolicy(DexteritySchemaPolicy):
    """Schema Policy for Video."""

    def bases(self, schema_name, tree):
        return (IVideo, )
