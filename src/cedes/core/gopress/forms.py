# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 by GoForWeb.be
#
# GNU General Public License (GPL)
#

from AccessControl import Unauthorized
from plone import api
from plone.z3cform.layout import wrap_form
from z3c.form import button
from z3c.form import field
from z3c.form import form
from z3c.form.contentprovider import ContentProviders
from z3c.form.interfaces import IFieldsAndContentProvidersForm
from zope import interface
from zope.browserpage.viewpagetemplatefile import ViewPageTemplateFile
from zope.contentprovider.provider import ContentProviderBase
from zope.interface import implementer


def compute_gopress_article_id(article_ids):
    """ """
    res = ''
    if len(article_ids) == 1:
        res = article_ids[0].split('-')[1]
    else:
        for article in article_ids:
            res += article.split('-')[1] + '-'
    res = res.strip('-')
    return res


class IGopressImport(interface.Interface):
    """ """


class GopressProvider(ContentProviderBase):
    """
      This ContentProvider will display the entire form.
    """
    template = \
        ViewPageTemplateFile('templates/gopress.pt')

    def __init__(self, context, request, view):
        super(GopressProvider, self).__init__(context, request, view)
        self.__parent__ = view
        self.portal_url = api.portal.get().absolute_url()

    def render(self):
        return self.template()


@implementer(IFieldsAndContentProvidersForm)
class GopressImportForm(form.Form):
    """
      This form will manage the gopress import
    """

    fields = field.Fields(IGopressImport)
    ignoreContext = True  # don't use context to get widget data

    contentProviders = ContentProviders()
    contentProviders['gopress'] = GopressProvider
    # put the 'gopress' in first position
    contentProviders['gopress'].position = 0
    label = "Importer un article depuis Gopress"
    description = ''
    _redirect_to = ''

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.portal = api.portal.get()
        self.portal_url = self.portal.absolute_url()

    def _check_auth(self):
        """Raise Unauthorized if current user can not use gopress."""
        member = api.user.get_current()
        if not member.is_manager():
            raise Unauthorized

    def update(self):
        """ """
        self._check_auth()
        super(GopressImportForm, self).update()
        # after calling parent's update, self.actions are available
        # hide buttons 'synchronize' and 'cancel', it is managed manually
        self.actions.get('synchronize').addClass('hidden')
        self.actions.get('cancel').addClass('hidden')
        # make import buttons primary
        self.actions.get('import').addClass('btn-primary')
        self.actions.get('group_html_import').addClass('btn-primary')
        self.actions.get('group_pdf_import').addClass('btn-primary')
        self.actions.get('group_html_pdf_import').addClass('btn-primary')

    def updateWidgets(self):
        # manipulate self.fields BEFORE doing form.Form.updateWidgets
        form.Form.updateWidgets(self)

    def render(self):
        if self._redirect_to:
            self.request.response.redirect(self._redirect_to)
            return ""
        return super(GopressImportForm, self).render()

    @button.buttonAndHandler('Synchroniser la liste avec Gopress', name='synchronize')
    def handle_synch_gopress(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return
        self._do_synch_gopress()

    def _do_synch_gopress(self):
        """ """
        self._check_auth()
        # synchronize
        sync_status = self.context.restrictedTraverse('@@gopress').synchronize()
        api.portal.show_message(
            "Synchronisation effectuée: tot art=%d, nouveau=%d, erreurs=%d." % (
                sync_status['art_count'],
                sync_status['new_art'],
                len(sync_status['errors'])),
            request=self.request)
        if sync_status['warns']:
            api.portal.show_message(
                u'%s' % (' | '.join(sync_status['warns'])),
                type='warning',
                request=self.request)
        if sync_status['errors']:
            api.portal.show_message(
                u'Erreurs Gopress pour: %s' % (' | '.join(sync_status['errors'])),
                type='error',
                request=self.request)
        self._redirect_to = self.request['URL']

    @button.buttonAndHandler("Annuler", name='cancel')
    def handle_cancel(self, action):
        self._redirect_to = self.context.absolute_url()

    @button.buttonAndHandler('Importer', name='import')
    def handle_import(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return
        # auth, validate, import
        self._check_auth()
        article_id, article_selection = self._validate_import()
        if article_id:
            self._do_import(article_id, article_selection)

    def _validate_import(self):
        """ """
        article_selection = self.request.form.get('form.widgets.article_selection', [])
        if not article_selection or len(article_selection) != 1:
            api.portal.show_message(
                'Veuillez sélectionner un seul article à importer.',
                type='warning',
                request=self.request)
            return None, None

        article_id = compute_gopress_article_id(article_selection)
        if hasattr(self.context, article_id):
            api.portal.show_message(
                'Cet article a déjà été importé dans le répertoire courant. '
                'Veuillez choisir un autre article.',
                type='warning',
                request=self.request)
            return None, None
        return article_id, article_selection

    def _do_import(self, article_id, article_selection):
        """ """
        folder_id = article_selection[0].split('-')[0]
        self.context.restrictedTraverse('@@xml-to-plone').upload_article(
            folder_id, article_id)
        api.portal.show_message('Article importé.', request=self.request)
        self._redirect_to = "{0}/{1}/view".format(
            self.context.absolute_url(), article_id)

    @button.buttonAndHandler('Grouper le HTML et importer', name='group_html_import')
    def handle_group_html_import(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return
        # auth, validate, import
        self._check_auth()
        article_selection, article_id = self._validate_group_import()
        if article_id:
            self._do_group_html_import(article_selection, article_id)

    def _validate_group_import(self):
        """ """
        article_selection = self.request.form.get('form.widgets.article_selection', [])
        if not article_selection or len(article_selection) <= 1:
            api.portal.show_message(
                'Veuillez sélectionner au moins deux articles à grouper et importer',
                type='warning',
                request=self.request)
            return None, None

        article_id = compute_gopress_article_id(article_selection)
        if hasattr(self.context, article_id):
            api.portal.show_message(
                'Cet article a déjà été importé dans le répertoire courant. '
                'Veuillez choisir un autre article.',
                type='warning',
                request=self.request)
            return None, None
        return article_selection, article_id

    def _do_group_html_import(self, article_selection, article_id):
        """ """
        articles_and_folder_ids = []
        for item in article_selection:
            order = int(self.request.get(item, 0))
            item_split = item.split("-")
            articles_and_folder_ids.append((order, item_split[1], item_split[0]))

        # sort ids according to order
        articles_and_folder_ids.sort()
        import_view = self.context.restrictedTraverse('@@xml-to-plone')
        if self.request.get("form.buttons.group_html_import", ""):
            import_view.merge_and_upload_articles(
                article_id, articles_and_folder_ids, option="html")
        elif self.request.get("form.buttons.group_pdf_import", ""):
            import_view.merge_and_upload_articles(
                article_id, articles_and_folder_ids, option="pdf")
        else:
            # button group_html_pdf_import
            import_view.merge_and_upload_articles(
                article_id, articles_and_folder_ids, option="htmlpdf")

        api.portal.show_message('Article importé.', request=self.request)
        self._redirect_to = "{0}/{1}/view".format(
            self.context.absolute_url(), article_id)

    @button.buttonAndHandler('Grouper les PDF et importer', name='group_pdf_import')
    def handle_group_pdf_import(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return
        # auth, validate, import
        self._check_auth()
        article_selection, article_id = self._validate_group_import()
        if article_id:
            self._do_group_html_import(article_selection, article_id)

    @button.buttonAndHandler('Grouper HTML&PDF et importer', name='group_html_pdf_import')
    def handle_group_html_pdf_import(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return
        # auth, validate, import
        self._check_auth()
        article_selection, article_id = self._validate_group_import()
        if article_id:
            self._do_group_html_import(article_selection, article_id)


GopressImportFormWrapper = wrap_form(GopressImportForm)
