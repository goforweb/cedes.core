# -*- coding: utf-8 -*-

from cedes.core import logger
from cedes.core.memberdata import CedesMemberData
from DateTime import DateTime
from plone import api
from plone.app.users.browser import membersearch
from plone.app.users.browser.membersearch import IMemberSearchSchema
from plone.app.users.browser.membersearch import MemberSearchForm
from plone.supermodel import model
from Products.CMFPlone import PloneMessageFactory as _
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.PlonePAS.plugins.property import ZODBMutablePropertyProvider
from Products.PlonePAS.plugins.property import isStringType
from z3c.form import button
from zope import schema
from zope.component import getMultiAdapter
from Products.PlonePAS.utils import safe_unicode


# monkey patch the extractCriteriaFromRequest to manage our usecases
membersearch.__old__extractCriteriaFromRequest = membersearch.extractCriteriaFromRequest


def extractCriteriaFromRequest(criteria):
    """ """
    for key in tuple(criteria.keys()):
        if key in ['_authenticator', 'form.buttons.search'] or \
           key.endswith('-empty-marker'):
            del criteria[key]
    for (key, value) in list(criteria.items()):
        if not value:
            del criteria[key]
        else:
            new_key = key.replace('form.widgets.', '')
            if value == ['selected']:
                value = True
            if isinstance(value, (tuple, list)):
                value = value[0]
            criteria[new_key] = value
            del criteria[key]
    # manage dates
    for key in criteria:
        if key.endswith('_time'):
            criteria[key] = (DateTime(criteria[key]), DateTime())
    return criteria


membersearch.extractCriteriaFromRequest = extractCriteriaFromRequest
logger.info("Monkey patching plone.app.users.membersearch (extractCriteriaFromRequest)")


# monkey patch the testMemberData to manage search on DateTime
ZODBMutablePropertyProvider.__old__testMemberData = ZODBMutablePropertyProvider.testMemberData


def testMemberData(self, memberdata, criteria, exact_match=False):
    """Test if a memberdata matches the search criteria.
    """
    from DateTime import DateTime
    for (key, value) in criteria.items():
        testvalue = memberdata.get(key, None)
        if testvalue is None:
            return False

        if isStringType(testvalue):
            testvalue = safe_unicode(testvalue.lower())
        if isStringType(value):
            value = safe_unicode(value.lower())

        if exact_match:
            if value != testvalue:
                return False
        else:
            try:
                # XXX begin changes by CeDES
                if isinstance(testvalue, DateTime) and isinstance(value, tuple):
                    return testvalue > value[0] and testvalue < value[1]
                # XXX end changes by CeDES
                if value not in testvalue:
                    return False
            except TypeError:
                # Fall back to exact match if we can check for
                # sub-component
                if value != testvalue:
                    return False
    return True


ZODBMutablePropertyProvider.testMemberData = testMemberData
logger.info("Monkey patching Products.PlonePAS.plugins.property.ZODBMutablePropertyProvider (testMemberData)")


class ICeDESMemberSearchSchema(IMemberSearchSchema):
    """Provide schema for member search."""

    model.fieldset(
        'extra',
        label=_(u'legend_member_search_criteria',
                default=u'User Search Criteria'),
        fields=['member_type',
                'school_name',
                'school_postal_code',
                'bill_name',
                'last_login_time',
                'has_failed_accounting_f',
                'has_failed_accounting_n',
                'has_bill_waiting_payment'])

    # override login for now to change label from u'Name' to u'User Name'
    login = schema.TextLine(
        title=_(u'label_user_name', default=u'User Name'),
        description=_(
            u'help_search_name',
            default=u'Find users whose login name contain'),
        required=False,
    )

    member_type = schema.Choice(
        title=_(u'label_member_type', default=u'Member type'),
        values=["", "CeDES Free", "CeDES 100%"],
        default='',
        required=True)
    school_name = schema.TextLine(
        title=_(u'label_school_name', default=u'School name'),
        required=False)
    school_postal_code = schema.TextLine(
        title=_(u'label_school_postal_code', default=u'School postal code'),
        required=False)
    bill_name = schema.TextLine(
        title=_(u'label_bill_name', default=u'Bill name'),
        required=False)
    last_login_time = schema.Date(
        title=_(u'label_last_login', default=u'Last login'),
        required=False)
    has_failed_accounting_f = schema.Bool(
        title=_(u'label_has_failed_accounting_f', default=u'Has failed accounting f'),
        required=False)
    has_failed_accounting_n = schema.Bool(
        title=_(u'label_has_failed_accounting_n', default=u'Has failed accounting n'),
        required=False)
    has_bill_waiting_payment = schema.Bool(
        title=_(u'label_has_bill_waiting_payment', default=u'Has bill waiting payment'),
        required=False)


class CeDESMemberSearchForm(MemberSearchForm):
    """ """

    # disable to ease back to search form results after actions (member credit, ...)
    enableCSRFProtection = False

    # use GET instead POST so we have parameters in URL and it is easier to come back to it
    method = 'get'

    schema = ICeDESMemberSearchSchema
    template = ViewPageTemplateFile('templates/membersearch_form.pt')

    @button.buttonAndHandler(_(u'label_search', default=u'Search'),
                             name='search')
    def handleApply(self, action):
        """ """
        super(CeDESMemberSearchForm, self).handleApply(self, action)
        if self.results:
            self.now = DateTime()
            ploneview = getMultiAdapter((self.context, self.request), name='plone')
            self.toLocalizedTime = ploneview.toLocalizedTime
            # complete results data
            portal = api.portal.get()
            properties_storage = portal.acl_users.mutable_properties._storage
            for user_info in self.results:
                if user_info['login'] in properties_storage:
                    user_info.update(properties_storage.get(user_info['login']))
                # expiration_date and last_payment_date are not stored
                user_info['expiration_date'] = \
                    CedesMemberData.get_expiration_date(
                        CedesMemberData.get_last_payment_date(
                            user_info['account_bills']))
