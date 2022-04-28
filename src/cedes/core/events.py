# -*- coding: utf-8 -*-

from cedes.core import logger
from cedes.core.interfaces import IThemeFacetedNavigable
from cedes.core.utils import get_modified_attrs
from cedes.core.utils import send_mail
from datetime import datetime
from DateTime import DateTime
from eea.facetednavigation.interfaces import IHidePloneLeftColumn
from eea.facetednavigation.layout.interfaces import IFacetedLayout
from persistent.list import PersistentList
from plone import api
from zope.annotation import IAnnotations
from zope.globalrequest import getRequest
from zope.interface import alsoProvides
from zope.interface import noLongerProvides


def onThemeAdded(theme, event):
    """Called when new theme added."""
    # enable faceted navigation and configure it
    theme.unrestrictedTraverse('@@faceted_subtyper').enable()
    IFacetedLayout(theme).update_layout('faceted-theme-view')
    # show the left portlets
    if IHidePloneLeftColumn.providedBy(theme):
        noLongerProvides(theme, IHidePloneLeftColumn)
    # remove every criteria as we use criteria stored on PlanClassement
    annotations = IAnnotations(theme)
    annotations['FacetedCriteria'] = PersistentList()
    alsoProvides(theme, IThemeFacetedNavigable)
    logger.info('Faceted navigation enabled for {0}'.format(
        '/'.join(theme.getPhysicalPath())))


def onThemeModified(theme, event):
    """Called when existing theme modified."""
    mod_attrs = get_modified_attrs(event)
    if 'title' in mod_attrs or 'IDublinCore.subjects' in mod_attrs:
        # reindex associated resources as theme title and description
        # is indexed in resources SearchableText
        associated = theme.get_associated_resources(sorted=False)
        for item in associated:
            item = item.getObject()
            item.reindexObject(idxs=['SearchableText'])


def onResourceModified(obj, event):
    """Called when existing resource modified."""
    # set a first classification date if empty and a classification is defined
    if not obj.cr_first_classification_date and obj.cr_classification:
        obj.cr_first_classification_date = datetime.now()
    # remove first classification date if no more classification
    elif not obj.cr_classification:
        obj.cr_first_classification_date = None


def onResourceLiked(obj, event):
    """ """
    obj.reindexObject(idxs=['user_ratings'])


def onResourceUnliked(obj, event):
    """ """
    obj.reindexObject(idxs=['user_ratings'])


def onPrincipalCreated(event):
    """Setup new member."""
    # set registration_date (used as a "created" attribute)
    member = api.user.get(event.object.getId())
    member.set_registration_date(DateTime())

    # send email to administrator
    request = getRequest()
    form = request.form
    send_mail(subject='Cedes - Nouvelle inscription',
              template_name='mail_newmember_template',
              options={'username': form['form.widgets.username'],
                       'fullname': form['form.widgets.fullname'],
                       'email': form['form.widgets.email'],
                       'school_name': form['form.widgets.school_name'],
                       'school_phone': form['form.widgets.school_phone'], })

    # asks for a bill if member is "CeDES 100%"
    # here member properties are still not set so get member_type from request
    if not request.form['form.widgets.member_type'] == ['CeDES Free']:
        member.bill_credits()


def onPrincipalDeleted(event):
    """ """
    pass


def onUserInitialLogin(event):
    """Set the member first_login_time."""
    api.user.get(event.object.getId()).set_first_login_time(DateTime())
