# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 by GoForWeb.be
#
# GNU General Public License (GPL)
#

from cedes.core import logger
from DateTime import DateTime
from plone.app.users import schema as pau_schema
from plone.autoform import directives
from Products.CMFPlone import PloneMessageFactory as _
from Products.PlonePAS.tools.memberdata import MemberData
from zope import schema
from zope.interface import Interface


# need to monkey patch user schemas because it is not overridable as is

class ICeDESUserDataSchema(Interface):
    """
    """
    # XXX original values of IUserDataSchema
    fullname = pau_schema.ProtectedTextLine(
        title=_(u'label_full_name', default=u'Full Name'),
        description=_(u'help_full_name_creation',
                      default=u"Enter full name, e.g. John Smith."),
        required=False)
    email = pau_schema.ProtectedEmail(
        title=_(u'label_email', default=u'Email'),
        description=u'We will use this address if you need to recover your '
                    u'password',
        required=True,
        constraint=pau_schema.checkEmailAddress,
    )

    # member type and legal validation
    directives.write_permission(member_type="cmf.ManagePortal")
    member_type = schema.Choice(
        title=_(u'label_member_type', default=u'Member type'),
        values=["CeDES Free", "CeDES 100%"],
        default='CeDES Free',
        required=True)
    legal_validation = schema.Bool(
        title=_(u'label_legal_validation', default=u'Legal validation'),
        required=True,
        default=False)

    # school
    school_name = schema.TextLine(
        title=_(u'label_school_name', default=u'School name'),
        required=False)
    school_email = schema.TextLine(
        title=_(u'label_school_email', default=u'School email'),
        constraint=pau_schema.checkEmailAddress,
        required=True)
    school_address = schema.TextLine(
        title=_(u'label_school_address', default=u'School address'),
        required=False)
    school_postal_code = schema.TextLine(
        title=_(u'label_school_postal_code', default=u'School postal code'),
        required=False)
    school_locality = schema.TextLine(
        title=_(u'label_school_locality', default=u'School locality'),
        required=False)
    school_country = schema.Choice(
        title=_(u'label_school_locality', default=u'School locality'),
        vocabulary='cedes.core.vocabularies.countriesvocabulary',
        default='BE',
        required=True)
    school_phone = schema.TextLine(
        title=_(u'label_school_phone', default=u'School phone'),
        required=False)

    # bill
    bill_use_tva = schema.Bool(
        title=_(u'label_bill_use_tva', default=u'Bill use tva'),
        required=False)
    bill_tva = schema.TextLine(
        title=_(u'label_bill_tva', default=u'Bill tva'),
        required=False)
    bill_name = schema.TextLine(
        title=_(u'label_bill_name', default=u'Bill name'),
        required=False)
    bill_email = schema.TextLine(
        title=_(u'label_bill_email', default=u'Bill email'),
        constraint=pau_schema.checkEmailAddress,
        required=True)
    bill_address = schema.TextLine(
        title=_(u'label_bill_address', default=u'Bill address'),
        required=False)
    bill_postal_code = schema.TextLine(
        title=_(u'label_bill_postal_code', default=u'Bill postal code'),
        required=False)
    bill_locality = schema.TextLine(
        title=_(u'label_bill_locality', default=u'Bill locality'),
        required=False)
    bill_country = schema.Choice(
        title=_(u'label_bill_locality', default=u'Bill locality'),
        vocabulary='cedes.core.vocabularies.countriesvocabulary',
        default='BE',
        required=True)


pau_schema.IUserDataSchema = ICeDESUserDataSchema
logger.info("Monkey patching plone.app.users.schema (IUserDataSchema)")


class CedesMemberData(MemberData):
    """ """

    account_transactions = {}

    def check_balance(self, price):
        """
          Checks if we can afford a purchase's price
          Returns True if balance > price, False otherwise
        """
        if "Manager" in self.getRoles():
            return True
        if self.get_balance() - price >= 0:
            return True
        else:
            return False

    def check_viewable(self, article_uid):
        """
          Check if the article can still be viewed.
          An element is viewable when his UID is found in member transactions
        """
        res = "Manager" in self.getRoles()
        if not res:
            inversed_transactions = tuple(reversed(self.account_transactions))
            for tr_uid, tr_price, tr_date in inversed_transactions:
                if tr_uid == article_uid:
                    res = True
        return res

    def get_account_transactions(self):
        """ """
        return {}

    def get_first_login_time(self):
        """ """
        return DateTime()

    def get_balance(self):
        """ """
        if "Manager" in self.getRoles():
            return 1000
        return 0

    def is_cedes_free(self):
        """ """
        return self.getProperty('member_type') == "CeDES Free"

    def add_transaction(self, article_uid, article_price=1, is_dossier_structure=False):
        """ """
        if not("Manager" in self.getRoles()):
            # an article is payed one time then accessed
            # but for DossierStructure, if it has been updated, the price is adapted and
            # the pdf is no more accessible
            if not is_dossier_structure and self.check_viewable(article_uid):
                return None
            previous_balance = self.get_balance()
            self.account_balance -= article_price
            if previous_balance >= 20 and self.account_balance < 20:
                self.send_low_reminder()
            self.account_transactions = self.account_transactions + \
                ((article_uid, article_price, DateTime()), )
        return None

    def get_transactions(self):
        """ """
        return []

    def get_last_payment_date(self):
        '''
          Returns the Date of the last time the account payment was validated.
          Returns None if the account was never credited
        '''
        last_payment_date = self.getProperty('last_payment_date')
        return last_payment_date if last_payment_date.year() != 1950 else None
        #if self.account_bills:
        #    bill_reversed = tuple(reversed(self.account_bills))
        #    for item in bill_reversed:
        #        if item['payment_date'] is not None and item['mode'] == "F":
        #            return item['payment_date']
        #return None

    @staticmethod
    def get_expiration_date(last_payment_date):
        '''
          Returns the expiration date (last payment date + 365 days).
          Returns None if the account was never credited.
        '''
        if last_payment_date is not None:
            return last_payment_date + 365
        return None

    def send_low_reminder(self):
        """ """
        # XXX
        return
        skintool = getToolByName(self, 'portal_skins')
        mailHost = getToolByName(self, 'MailHost')
        email = skintool.cedes_emails.credit_low_notification(
            self.REQUEST,
            fullname=self.fullname,
            firstname=self.firstname,
            member_email=self.email,
            balance=self.getBalance())
        mailHost.send(email.encode('utf-8'))
        return True
