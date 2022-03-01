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
from plone import api

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

    def get_account_bills(self):
        """ """
        return self.getProperty('account_bills')

    def get_account_transactions(self):
        """ """
        return self.getProperty('account_transactions')

    def set_account_bills(self, account_bills):
        """ """
        self.setMemberProperties({'account_bills': account_bills})

    def set_account_transactions(self, account_transactions):
        """ """
        self.setMemberProperties({'account_transactions': account_transactions})

    def get_account_balance(self):
        """ """
        if "Manager" in self.getRoles():
            return 1000
        else:
            return self.getProperty('account_balance')

    def set_account_balance(self, account_balance):
        """ """
        self.setMemberProperties({'account_balance': account_balance})

    def get_member_type(self):
        """ """
        return self.getProperty('member_type')

    def set_member_type(self, member_type):
        """ """
        self.setMemberProperties({'member_type': member_type})

    def get_bill_accounting_failed(self):
        """ """
        return self.getProperty('bill_accounting_failed')

    def set_bill_accounting_failed(self, total, mode, now):
        """ """
        self.setMemberProperties({'bill_accounting_failed': (total, mode, now)})
        if mode == "F":
            self.setMemberProperties({'has_failed_accounting_f': True})
        else:
            self.setMemberProperties({'has_failed_accounting_n': True})

    def check_balance(self, price):
        """
          Checks if we can afford a purchase's price
          Returns True if balance > price, False otherwise
        """
        if "Manager" in self.getRoles():
            return True
        if self.get_account_balance() - price >= 0:
            return True
        else:
            return False

    def credit(self, value):
        """ """
        self.set_account_balance(self.get_account_balance() + value)
        self.set_account_transactions(self.get_account_transactions() +
                                      (('Crédit', value, DateTime()),))
        # email notification
        #skintool = getToolByName(self, 'portal_skins')
        #mailHost = getToolByName(self, 'MailHost')
        #email = skintool.cedes_emails.credit_activation_notification(
        #   self.REQUEST, member_email=self.email, firstname=self.firstname, credit=value)
        #mailHost.send(email.encode('utf-8'))

    def request_credit(self):
        """ """
        if self.is_cedes_free():
            return False
        else:
            self.bill_credits()
            # check if a Manager is renewing the subscription for a member
            # in this case, the current member id is different from the self.id
            current_user_id = api.user.get_current().getId()
            if current_user_id == self.getId():
                self.send_credit_request_confirmation()
            return True

    def bill_credits(self, total="3000", mode="F"):
        """ """
        now = DateTime()
        self.set_bill_accounting_failed(total, mode, now)
        #skinTool = getToolByName(self, 'portal_skins')
        #mailHost = getToolByName(self, 'MailHost')
        #error_text = "SERVEUR INDISPONIBLE, L'application Cedes tentera de se " \
        #    "reconnecter à l'application comptable plus tard."
        #email = skinTool.cedes_emails.registration_error_manager(
        #    self.REQUEST, member_id=bill_id, error_text=error_text)
        #mailHost.send(email.encode('utf-8'))
        return False

    def check_viewable(self, article_uid):
        """
          Check if the article can still be viewed.
          An element is viewable when his UID is found in member transactions
        """
        res = "Manager" in self.getRoles()
        if not res:
            inversed_transactions = tuple(reversed(self.get_account_transactions()))
            for tr_uid, tr_price, tr_date in inversed_transactions:
                if tr_uid == article_uid:
                    res = True
        return res

    def get_first_login_time(self):
        """ """
        return DateTime()

    def is_cedes_free(self):
        """ """
        return self.getProperty('member_type') == "CeDES Free"

    def add_bill(self, bill_id, price=3000, mode='F', date=None, payment_date=None):
        """ """
        date = date or DateTime()
        self.set_account_bills(
            self.get_account_bills() +
            ({'bill_id': bill_id,
              'price': price,
              'mode': mode,
              'date': date,
              'payment_date': payment_date},))

    def add_transaction(self, article_uid, article_price=1, is_dossier_structure=False):
        """ """
        if "Manager" not in self.getRoles():
            # an article is payed one time then accessed
            # but for DossierStructure, if it has been updated, the price is adapted and
            # the pdf is no more accessible
            if not is_dossier_structure and self.check_viewable(article_uid):
                return None
            previous_balance = self.get_account_balance()
            self.set_account_balance(previous_balance - article_price)
            if previous_balance >= 20 and self.get_account_balance() < 20:
                self.send_low_reminder()
            self.set_account_transactions(
                self.get_account_transactions() +
                ((article_uid, article_price, DateTime()), ))
        return None

    def validate_payment(self, now=None):
        """ """
        now = now or DateTime()
        if self.get_bill_waiting_payment():
            self.get_account_bills()[-1]['payment_date'] = now
            self.set_payment_notification_date(None)
            self.set_expiration_notification_date(None)
            return True
        return False

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

    def get_bill_waiting_payment(self):
        '''
          Returns bill_id of the bill waiting for a payment
          Returns None if no bill is waiting for payment
        '''
        if len(self.get_account_bills()) > 0:
            item = self.get_account_bills()[-1]
            if item['payment_date'] is None and \
               item['date'] is not None and \
               item['mode'] == 'F':
                return item
        return None

    @staticmethod
    def get_expiration_date(last_payment_date):
        '''
          Returns the expiration date (last payment date + 365 days).
          Returns None if the account was never credited.
        '''
        if last_payment_date is not None:
            return last_payment_date + 365
        return None

    def set_payment_notification_date(self, date=None):
        """ """
        self.setMemberProperties({'payment_notification_date': date})

    def set_expiration_notification_date(self, date=None):
        """ """
        self.setMemberProperties({'expiration_notification_date': date})

    def send_low_reminder(self):
        """ """
        #skintool = getToolByName(self, 'portal_skins')
        #mailHost = getToolByName(self, 'MailHost')
        #email = skintool.cedes_emails.credit_low_notification(
        #    self.REQUEST,
        #    fullname=self.fullname,
        #    firstname=self.firstname,
        #    member_email=self.email,
        #    balance=self.getBalance())
        #mailHost.send(email.encode('utf-8'))
        return True

    def send_credit_request_confirmation(self):
        """ """
        #skintool = getToolByName(self, 'portal_skins')
        #mailHost = getToolByName(self, 'MailHost')
        #email = skintool.cedes_emails.credit_request_confirmation(self.REQUEST, fullname=self.fullname, firstname=self.getFirstname(), member_email=self.email)
        #mailHost.send(email.encode('utf-8'))
        return True