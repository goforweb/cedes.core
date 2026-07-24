# -*- coding: UTF-8 -*-

from Acquisition import aq_inner
from cedes.core.utils import uuidToObject
from plone.base.defaultpage import check_default_page_via_view
from Products.CMFPlone import utils
from Products.CMFPlone.browser.interfaces import INavigationBreadcrumbs
from Products.CMFPlone.browser.navigation import get_view_url
from Products.CMFPlone.browser.navigation import PhysicalNavigationBreadcrumbs
from Products.CMFPlone.browser.navtree import get_navigation_root
from Products.CMFPlone.interfaces import IHideFromBreadcrumbs
from zope.component import getMultiAdapter
from zope.interface import implementer


# Calculate breadcrumbs based on classification scheme instead of physical folders
# Breadcrumbs showing the first classification associated  with a content type
# results should be a list of dict
@implementer(INavigationBreadcrumbs)
class ClassificationBreadcrumbs(PhysicalNavigationBreadcrumbs):

    def breadcrumbs(self):
        context = aq_inner(self.context)
        request = aq_inner(self.request)

        # begin changes by cedes.core
        ct_uid = request.get('bc', None)
        if ct_uid:  # if we provide an uid of the container in the request object
            container = uuidToObject(ct_uid, unrestricted=True)
        elif hasattr(context, 'cr_classification'):
            ct = context.cr_classification
            if ct:  # we use the first classification associated with the content
                container = ct[0].to_object
            else:  # we get the REAL parent of the object
                container = utils.parent(context)
        else:  # we get the REAL parent of the object
            container = utils.parent(context)
        # end changes by cedes.core

        try:
            name, item_url = get_view_url(context)
        except AttributeError:
            print(context)
            raise

        if container is None:
            return ({'absolute_url': item_url,
                     'Title': utils.pretty_title_or_id(context, context), },)

        view = getMultiAdapter((container, request), name='breadcrumbs_view')
        base = tuple(view.breadcrumbs())

        # Some things want to be hidden from the breadcrumbs
        if IHideFromBreadcrumbs.providedBy(context):
            return base

        if base:
            item_url = '%s/%s' % (base[-1]['absolute_url'], name)

        rootPath = get_navigation_root(context)
        itemPath = '/'.join(context.getPhysicalPath())

        # don't show default pages in breadcrumbs or pages above the navigation
        # root
        if not check_default_page_via_view(
            context, request
        ) and not rootPath.startswith(itemPath):
            entry = {
                "absolute_url": item_url,
                "Title": utils.pretty_title_or_id(context, context),
            }
            self.customize_entry(entry, context)
            base += (entry,)

        return base
