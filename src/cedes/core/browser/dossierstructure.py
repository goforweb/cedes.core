# -*- coding: utf-8 -*-

from cedes.core.pisa import generate_pdf
from cedes.core.pisa import pdf
from collections import OrderedDict
from plone import api
from plone.dexterity.browser.view import DefaultView
from Products.Five import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

import re


class DossierStructurePDF(BrowserView):
    """ """

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.portal = api.portal.get()
        self.wf_tool = api.portal.get_tool('portal_workflow')
        self.portal_catalog = api.portal.get_tool('portal_catalog')

    def get_resources(self, point):
        """ """
        return [elt for elt in point.get_cf_resources(the_objects=True)
                if self.wf_tool.getInfoFor(elt, 'review_state') != 'private']

    def clean_htmlforpdf(self, html, explicit=False):
        """ """
        if explicit:
            html = self.replace_links_explicit(html)

        html = html.replace('<h1', '<span')
        html = html.replace('<h2', '<span')
        html = html.replace('<h3', '<span')
        html = html.replace('<h4', '<span')
        # h5 is the style used for "intertitre", must be bold
        html = html.replace('<h5', '<b style="display:block"')
        html = html.replace('<h6', '<span')

        html = html.replace('</h1', '</span')
        html = html.replace('</h2', '</span')
        html = html.replace('</h3', '</span')
        html = html.replace('</h4', '</span')
        html = html.replace('</h5', '</b')
        html = html.replace('</h6', '</span')

        html = self.replace_uid_links_url(html)
        return html

    def replace_links_explicit(self, html):
        """ """
        pattern = r"""<a href="(.*?)">\s*((\n|.)+?)\s*</a>"""
        return re.sub(pattern, self.get_links_explicit, html)

    def get_links_explicit(self, html):
        href = html.group(1)
        link = [href[i: i+80] for i in range(0, len(href), 80)]
        content = html.group(2)
        return content + '<pdf:keeptogether> <a style="font-family:Courier New" href="' + \
            href + '"><br/>' + '<br/>'.join(link) + '<br/></a></pdf:keeptogether>'

    def replace_uid_links_url(self, html):
        """ """
        pattern = r'"resolveuid/(\w*?)"'
        # sub function: first param is pattern to search, second is a function
        # to call on the token as a replacement, thirs is source
        return re.sub(pattern, self.get_token_url, html)

    def get_token_url(self, html):
        tokenString = html.group()
        tokenUID = tokenString[12:-1]
        tokenId = self.portal_catalog(UID=tokenUID)
        if len(tokenId) == 0:
            tokenId = '"' + tokenUID + '"'
        else:
            tokenId = tokenId[0].getURL()
        return '"' + tokenId + '"'

    def clean_linkforpdf(self, url):
        """ """
        url = [url[i: i+80] for i in range(0, len(url), 80)]
        return '<br/>'.join(url)


def get_dossier_structure(context):
    ''' '''
    parent = context
    while parent.portal_type != 'DossierStructure':
        parent = parent.aq_inner.aq_parent
    return parent


def get_html_toc(context, data=None, prefix=''):
    """ """
    portal_url = api.portal.get().absolute_url()
    member = api.user.get_current()
    is_manager = member.has_role('Manager')
    res = data or OrderedDict()
    subitems = [obj for obj in context.objectValues()
                if obj.portal_type in ['Point', 'Link']]
    ds = get_dossier_structure(context)
    start_from = ds.start_numbering_at - 1
    wf_tool = api.portal.get_tool('portal_workflow')
    for i in range(len(subitems)):
        item = subitems[i]
        item_uid = item.UID()
        item_state = wf_tool.getInfoFor(item, 'review_state')
        res[item_uid] = {}
        if prefix != '':
            current_prefix = prefix + '.' + str(start_from + i + 1)
        else:
            current_prefix = str(start_from + i + 1)
        res[item_uid]['prefix'] = current_prefix
        title = current_prefix + " " + item.Title()
        css_class_level = len(current_prefix.split('.'))
        # highlight private items
        css_class_item_state = ''
        if item_state == 'private':
            css_class_item_state = ' state-private'
        opening_div = '<div class="item_level_{0}{1}">'.format(css_class_level, css_class_item_state)
        if item.portal_type == 'Point' and item.cf_resources:
            content = opening_div + '<a ' + 'class="{0}"'.format(css_class_item_state) + \
                ' href="' + item.absolute_url() + '">' + title + '</a>' + '</div>'
        elif item.portal_type == 'Link':
            if is_manager:
                item_url = item.absolute_url()
            else:
                item_url = item.getRemoteUrl()
            content = opening_div + '<a ' + 'class="{0}"'.format(css_class_item_state) + \
                ' href="' + item_url + '">' + title + '</a>' + \
                '&nbsp;<img src={0}/++plone++cedes.core/icon-external-link.png />'.format(
                    portal_url) + '</div>'
        else:
            content = opening_div + title + '</div>'
        res[item_uid]['content'] = content
        get_html_toc(item, res, prefix=current_prefix)
    return res


class HTMLTocView(BrowserView):
    """ """
    def __init__(self, context, request):
        '''
          Compute the HTML Toc dict.
        '''
        super(HTMLTocView, self).__init__(context, request)
        self.full_toc = get_html_toc(self.context.get_dossier_structure())
        if self.context.portal_type == 'Point':
            self.context_toc = self._compute_context_toc()

    def point_number(self, point):
        """ """
        return self.full_toc[point.UID()]['prefix']

    def point_title(self):
        """ """
        return '{0} {1}'.format(
            self.full_toc[self.context.UID()]['prefix'], self.context.Title())

    def _compute_context_toc(self):
        """ """
        # walk the full_toc, find the context UID then keep following
        # records if prefix starts with context prefix
        context_toc = OrderedDict()
        context_UID = self.context.UID()
        context_prefix = None
        for k, v in self.full_toc.items():
            if k == context_UID:
                context_prefix = v['prefix']
                continue
            if context_prefix and v['prefix'].startswith(context_prefix + "."):
                context_toc[k] = v
        return context_toc

    def display_full_toc(self):
        """ """
        return ViewPageTemplateFile("templates/full_toc.pt")(self)

    def display_context_toc(self):
        """ """
        return ViewPageTemplateFile("templates/context_toc.pt")(self)


class DossierStructureDefaultView(DefaultView):
    """ """

    def _update(self):
        super(DossierStructureDefaultView, self)._update()
        self.member = api.user.get_current()
        self.is_manager = self.member.has_role('Manager')
        self.is_cedes_free = self.member.is_cedes_free()
        self.has_credits = self.member.get_account_balance() > 0
        self.price = self.context.get_price()

    def may_access(self):
        return bool(not self.is_cedes_free and self.has_credits and self.price == 0) \
            or self.is_manager


class GeneratePDFView(BrowserView):
    """ """

    def __call__(self):
        """ """
        return generate_pdf(self.context)


class GetPDFView(BrowserView):
    """ """

    def __call__(self):
        """ """
        return pdf(self.context)
