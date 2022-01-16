# -*- coding: utf-8 -*-

from plone import api
from Products.Five import BrowserView


class DSPrice(BrowserView):

    TEMPLATE_FREE_DS = '<p class="description"><b>Dossier gratuit.</b></p>' \
                       '<a href="%s">Accéder à la table des matières du dossier</a>'
    TEMPLATE_PAYING_DS = '<p class="description"><b>Coût total du dossier : %d point(s).  Coût réel du dossier ' \
                         '(en fonction des articles qui ont déjà été débités de votre compte) : %d point(s).</b></p>' \
                         '<a href="%s">Accéder gratuitement à la table des matières du dossier</a>'

    def __call__(self, UID):
        """
          Return real price that would cost complete access the the given dossierstructure p_UID
          for the currently connected member.
        """
        catalog = api.portal.get_tool('portal_catalog')
        obj = catalog.unrestrictedSearchResults(UID=UID)[0].getObject()
        total = obj.get_price(total=True)
        if total == 0:
            return self.TEMPLATE_FREE_DS % obj.absolute_url()

        real = obj.get_price(total=False)
        return self.TEMPLATE_PAYING_DS % (total, real, obj.absolute_url())
