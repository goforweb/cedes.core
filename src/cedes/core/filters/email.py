# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 by GoForWeb.be
#
# GNU General Public License (GPL)
#


from plone.outputfilters.interfaces import IFilter
from zope.interface import implementer


@implementer(IFilter)
class Renderer(object):
    """Replace some contents identified by [[content_name]]."""

    order = 1000

    replacements = {
        "header": "<p>Cher membre,</p>",
        "footer": "<p>Bon travail,</p><p>L'équipe du CeDES</p>",
        "newsletter":
            "<p>Ce courriel pour vous informer des ressources introduites dans la base "
            "de données entre le {0} et le {1}.</p><p>Pour y accéder, cliquez sur "
            "le lien <a href='{2}' target='_blank'>{2}</a> pour être directement dirigé vers la liste des nouveautés.</p>"}

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def is_enabled(self):
        return True

    def __call__(self, data):
        for replacement, value in self.replacements.items():
            if replacement == "newsletter" and \
               self.context.newsletter_from and \
               self.context.newsletter_to:
                value = value.format(self.context.newsletter_from.strftime('%d/%m/%Y'),
                                     self.context.newsletter_to.strftime('%d/%m/%Y'),
                                     self.context.absolute_url())
            data = data.replace("[{0}]".format(replacement), value)
        return data
