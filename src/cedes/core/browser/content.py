# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 by GoForWeb.be
#
# GNU General Public License (GPL)
#

from cedes.core.utils import provoke_unauthorized
from plone import api
from plone.dexterity.browser.view import DefaultView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile


class BaseView(DefaultView):
    """ """

    def update(self):
        super(BaseView, self).update()
        self.member = api.user.get_current()
        if self.member.has_role('Anonymous'):
            provoke_unauthorized()
        self.portal = api.portal.get()
        self.portal_url = self.portal.absolute_url()

    def render_cr_first_classification_date(self):
        """ """
        return ViewPageTemplateFile("templates/common-first-classification-date.pt")(self)

    def render_common_content(self):
        """ """
        return ViewPageTemplateFile("templates/common-content.pt")(self)

    def render_description(self):
        """ """
        return ViewPageTemplateFile("templates/common-description.pt")(self)

    def render_file(self):
        """ """
        return ViewPageTemplateFile("templates/common-file.pt")(self)

    def render_html(self, fieldname):
        """ """
        self._html_fieldname = fieldname
        return ViewPageTemplateFile("templates/common-html.pt")(self)

    def render_link(self):
        """ """
        return ViewPageTemplateFile("templates/common-link.pt")(self)

    def render_references(self):
        """ """
        return ViewPageTemplateFile("templates/common-references.pt")(self)

    def link_infos(self):
        """Format the url for display."""
        view = self.context.unrestrictedTraverse('@@link_redirect_view')
        infos = view.display_link()
        if infos:
            infos.update({'absolute_url': view.absolute_target_url()})
        return infos


class AudioView(BaseView):
    """ """


class ArticleGratuitView(BaseView):
    """ """


class ArticlePayantView(BaseView):
    """ """

    def was_warned(self):
        """User must always have been warned before accessing a payint resource."""
        warned = False
        if self.request['HTTP_REFERER'].startswith(self.portal_url) and \
           'login?came_from' not in self.request['HTTP_REFERER']:
            warned = True
        return warned


class BibliographieView(BaseView):
    """ """


class EmailContentView(DefaultView):
    """ """

    def update(self):
        super(EmailContentView, self).update()
        self.member = api.user.get_current()
        if self.member.has_role('Anonymous'):
            provoke_unauthorized()
        if self.member.is_manager() and \
           getattr(self.context, '_email_sent_date', None) is not None:
            api.portal.show_message(
                'E-mail envoyé le {0}'.format(
                    self.context._email_sent_date.strftime('%d/%m/%Y (%H:%M)')),
                request=self.request, type="warning")


class PointView(DefaultView):
    """ """


class SequenceApprentissageView(BaseView):
    """ """


class SiteInternetView(BaseView):
    """ """


class StatistiquesView(BaseView):
    """ """


class VideoView(BaseView):
    """ """
