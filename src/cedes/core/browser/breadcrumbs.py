# -*- coding: UTF-8 -*-

from Acquisition import aq_base
from Acquisition import aq_inner
from cedes.core.utils import uuidToObject
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone import utils
from Products.CMFPlone.browser.interfaces import INavigationBreadcrumbs
from Products.CMFPlone.browser.navtree import getNavigationRoot
from Products.CMFPlone.interfaces import IHideFromBreadcrumbs
from Products.Five import BrowserView
from zope.component import getMultiAdapter
from zope.interface import implementer


##
# Calculate breadcrumbs based on classification scheme instead of physical folders
##



def get_url(item):
    if hasattr(aq_base(item), 'getURL'):
        # Looks like a brain
        return item.getURL()
    return item.absolute_url()


def get_id(item):
    getId = getattr(item, 'getId')
    if not utils.safe_callable(getId):
        # Looks like a brain
        return getId
    return getId()


def get_view_url(context):
    props = getToolByName(context, 'portal_properties')
    stp = props.site_properties
    view_action_types = stp.getProperty('typesUseViewActionInListings', ())

    item_url = get_url(context)
    name = get_id(context)

    if context.portal_type in view_action_types:
        item_url += '/view'
        name += '/view'

    return name, item_url


# Breadcrumbs showing the first classification associated  with a content type
# results should be a list of dict
@implementer(INavigationBreadcrumbs)
class ClassificationBreadcrumbs(BrowserView):

    def breadcrumbs(self):
        context = aq_inner(self.context)
        request = aq_inner(self.request)

        # XXX begin changes by cedes.core
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
        # XXX end changes

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

        rootPath = getNavigationRoot(context)
        itemPath = '/'.join(context.getPhysicalPath())

        # don't show default pages in breadcrumbs or pages above the navigation root
        if not utils.isDefaultPage(context, request) and not rootPath.startswith(itemPath):
            base += ({'absolute_url': item_url,
                      'Title': utils.pretty_title_or_id(context, context), },)

        return base
