# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 by GoForWeb.be
#
# GNU General Public License (GPL)
#

from cedes.core import logger
from cedes.core.utils import create_attachment
from cedes.core.utils import send_mail
from copy import deepcopy
from DateTime import DateTime
from plone import api
from plone.app.users import schema as pau_schema
from plone.autoform import directives
from Products.CMFPlone import PloneMessageFactory as _
from Products.PlonePAS.tools.memberdata import MemberData
from zope import schema
from zope.interface import Interface
from zope.interface import Invalid
from zope.interface import invariant
from zope.globalrequest import getRequest

import re


def legal_validation_constraint(value):
    """Must be True."""
    if value is not True:
        raise Invalid('Vous devez accepter la charte afin de pouvoir vous inscrire comme membre.')
    return True


def check_email_unicity(email):
    """Make sure an e-mail address is only used one time."""
    email = email.strip()
    # some domains may create several accounts
    BYPASSED_DOMAINS = ['@unamur.be', '@goforweb.be', '@fundp.ac.be']
    for domain in BYPASSED_DOMAINS:
        if domain in email:
            return True
    mTool = api.portal.get_tool('portal_membership')
    return bool(mTool.searchForMembers(email=email))


def check_tva_number(full_tva_num):
    """ """

    if len(full_tva_num) > 16:
        return False

    european_vat = {
        "AT": "AT U?\d{8}",
        "BE": "BE 0?\d{3}\.?\d{3}\.?\d{3}",
        "BG": "BG \d{9,10}",
        "CY": "CY \d{8}[A-Z0-9]",
        "CZ": "CZ \d{8,10}",
        "DE": "DE \d{9}",
        "DK": "DK \d\d \d\d \d\d \d\d",
        "EE": "EE \d{9}",
        "ES": "ES [A-Z0-9]\d{7}[A-Z0-9]",
        "FI": "FI \d{8}",
        "FR": "FR [A-Z0-9]{2}\d{9}",
        "GB": "GB \d{3} \d{4} \d{2}|GB \d{3} \d{4} \d{2} \d{3}|GB GD\d{3}|GB HA\d{3}",
        "GR": "EL \d{9}",
        "HU": "HU \d{8}",
        "IE": "IE \d[A-Z0-9+*]\d{5}[A-Z]",
        "IT": "IT \d{11}",
        "LT": "LT \d{9}|LT \d{12}",
        "LU": "LU \d{8}",
        "LV": "LV \d{11}",
        "MT": "MT \d{8}",
        "NL": "NL \d{9}B\d\d",
        "PL": "PL \d{10}",
        "PT": "PT \d{9}",
        "RO": "RO \d{2,10}",
        "SE": "SE \d{12}",
        "SI": "SI \d{8}",
        "SK": "SK \d{10}", }

    # Returns true if we dont have validator for this country
    country = full_tva_num[0:2]
    country_check = european_vat.get(country)
    if not(country_check):
        return True

    # checks vat according to regexpr
    match = re.search(country_check, full_tva_num, re.VERBOSE)
    if match is None:
        return False
    else:
        if country != "BE":
            return True
        else:
            # If belgian Number validates check digit
            full_tva_num = full_tva_num.replace(".", "").replace(" ", "")
            try:
                tva_num = int(full_tva_num[2:-2])
                check_digit = int(full_tva_num[-2:])
            except Exception:
                return False
            if 97 - (tva_num % 97) == check_digit:
                return True
    return False


class ICeDESUserDataSchema(Interface):
    """Need to monkey patch user schemas because it is not overridable as is."""
    # original values of IUserDataSchema
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
        constraint=legal_validation_constraint)

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
    bill_tva = schema.TextLine(
        title=_(u'label_bill_tva', default=u'Bill tva'),
        description=('Encodez votre numéro de TVA seulement si vous êtes assujetti'),
        required=False)
    bill_name = schema.TextLine(
        title=_(u'label_bill_name', default=u'Bill name'),
        required=False)
    bill_email = schema.TextLine(
        title=_(u'label_bill_email', default=u'Bill email'),
        constraint=pau_schema.checkEmailAddress,
        # managed using a validator because we use same form to manage Free account
        required=False)
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

    @invariant
    def validate_data(data):
        ''' '''
        # username is only available when registrating
        if len(getattr(data, 'username', '')) > 32:
            raise Invalid('L\'identifiant ne peut dépasser 32 caractères.')

        # if request.get("email")!= None and request.get("email").find("hotmail") > 1:
        #   state.setError('email', 'Pour des raisons techniques, nous ne pouvons actuellement
        # pas accepter les boites hotmail. Veuillez entrez une autre adresse email.')

        # check email unicity, 2 cases:
        # registering, then we can not found an email
        # editing personnal preferences or changing existing email, we may only find current member
        is_registering = getattr(data, 'username', False)
        if is_registering:
            if check_email_unicity(data.email):
                raise Invalid('Un compte est déjà lié à l\'adresse courriel "{0}". '
                              'Utilisez les procédures "Obtenir votre nom d\'utilisateur" et '
                              '"Réinitialiser votre mot de passe" disponible via le lien '
                              '"Se connecter" pour récupérer votre identifiant et '
                              'votre mot de passe.'.format(data.email))
        else:
            # editing email, only one may be found (myself) if not changing
            # and none may be found if changing
            req = getRequest()
            current_email = req.get('PUBLISHED').member.getProperty('email')
            if current_email.strip() != data.email.strip() and check_email_unicity:
                # changing email and reusing an existing one
                raise Invalid("L'adresse courriel \"{0}\" est déjà utilisée.".format(data.email))

        # if bill_... fields are shown and current member is not a Manager, it must be filled
        if not api.user.get_current().is_manager() and hasattr(data, 'bill_name'):
            if not data.bill_name or \
               not data.bill_email or \
               not data.bill_country or \
               not data.bill_address or \
               not data.bill_address or \
               not data.bill_postal_code or \
               not data.bill_locality or \
               not data.bill_locality:
                raise Invalid('Veuillez encoder tous les champs dans la zone "Facturation" au bas du formulaire.')

            if len(data.bill_name) > 64:
                raise Invalid('La champ "Nom pour facturation" ne peut dépasser 64 caractères.')

            if len(data.bill_address) > 64:
                raise Invalid('La champ "Adresse pour facturation" ne peut dépasser 64 caractères.')

            if len(data.bill_postal_code) > 64:
                raise Invalid('La champ "Code postal" ne peut dépasser 64 caractères.')

            if len(data.bill_locality) > 64:
                raise Invalid('La champ "Localité" ne peut dépasser 64 caractères.')

            # TVA validity
            if data.bill_tva:
                # Grèce is an exception to this rule
                if data.bill_tva[0:2] != data.bill_country and data.bill_tva[0:2] != 'GR':
                    raise Invalid('Votre numéro de TVA ne correspond pas au pays de l\'adresse de facturation. '
                                  'Veuillez entrer le numéro au complet en commençant par le code pays. '
                                  'Exemple pour la Belgique: BE0888923935.')
                elif check_tva_number(data.bill_tva) is not True:
                    raise Invalid('Votre numéro de TVA n\'est pas valide. '
                                  'Veuillez entrer votre numéro sans espace en commençant par le code pays. '
                                  'Exemple pour la Belgique: BE0888923935.')


pau_schema.IUserDataSchema = ICeDESUserDataSchema
logger.info("Monkey patching plone.app.users.schema (IUserDataSchema)")


class CedesMemberData(MemberData):
    """ """

    def Title(self):
        """ """
        return "{0} ({1})".format(self.getProperty('fullname'), self.getId())

    def get_fullname(self):
        """ """
        return deepcopy(self.getProperty('fullname'))

    def get_email(self):
        """ """
        return deepcopy(self.getProperty('email'))

    def get_account_bills(self):
        """ """
        return deepcopy(self.getProperty('account_bills'))

    def set_account_bills(self, account_bills):
        """ """
        self.setMemberProperties({'account_bills': account_bills})

    def get_account_transactions(self):
        """ """
        return deepcopy(self.getProperty('account_transactions'))

    def set_account_transactions(self, account_transactions):
        """ """
        self.setMemberProperties({'account_transactions': account_transactions})

    def get_account_balance(self):
        """ """
        if self.is_manager():
            return 1000
        else:
            return deepcopy(self.getProperty('account_balance'))

    def set_account_balance(self, account_balance):
        """ """
        self.setMemberProperties({'account_balance': account_balance})

    def get_member_type(self):
        """ """
        return deepcopy(self.getProperty('member_type'))

    def set_member_type(self, value):
        """ """
        self.setMemberProperties({'member_type': value})

    def get_registration_date(self):
        """ """
        return deepcopy(self.getProperty('registration_date'))

    def set_registration_date(self, value):
        """ """
        self.setMemberProperties({'registration_date': value})

    def get_first_login_time(self):
        """ """
        return deepcopy(self.getProperty('first_login_time'))

    def set_first_login_time(self, value):
        """ """
        self.setMemberProperties({'first_login_time': value})

    def get_bill_accounting_failed(self):
        """ """
        return deepcopy(self.getProperty('bill_accounting_failed'))

    def set_bill_accounting_failed(self, total, mode, now):
        """ """
        self.setMemberProperties({'bill_accounting_failed': (total, mode, now)})
        if mode == "F":
            self.setMemberProperties({'has_failed_accounting_f': True})
        else:
            self.setMemberProperties({'has_failed_accounting_n': True})

    def set_has_bill_waiting_payment(self, value):
        """ """
        self.setMemberProperties({'has_bill_waiting_payment': value})

    def check_balance(self, price):
        """
          Checks if we can afford a purchase's price
          Returns True if balance > price, False otherwise
        """
        if self.is_manager():
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
        send_mail(subject='CeDES - Vos crédits ont été activés',
                  template_name='mail_credit_activation',
                  options={'title': self.Title(),
                           'credit': value, },
                  mto=self.get_email())

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

    def request_100pc(self):
        """ """
        self.set_member_type("CeDES 100%")
        self.bill_credits()
        self.send_100pc_confirmation()

    def bill_credits(self, total="3000", mode="F"):
        """ """
        now = DateTime()
        self.set_bill_accounting_failed(total, mode, now)
        # email notification for Managers
        send_mail(
            subject="CeDES - Erreur de l'application comptable",
            template_name='mail_registration_error_manager',
            options={'member_id': self.getId(),
                     'error_text': "SERVEUR INDISPONIBLE, L'application CeDES tentera de se "
                     "reconnecter à l'application comptable plus tard.", })
        return False

    def is_manager(self):
        """ """
        return "Manager" in self.getRoles()

    def check_viewable(self, article_uid):
        """
          Check if the article can still be viewed.
          An element is viewable when his UID is found in member transactions
        """
        res = self.is_manager()
        if not res:
            inversed_transactions = tuple(reversed(self.get_account_transactions()))
            for tr_uid, tr_price, tr_date in inversed_transactions:
                if tr_uid == article_uid:
                    res = True
        return res

    def is_cedes_free(self):
        """ """
        return self.get_member_type() == "CeDES Free"

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
        self.set_has_bill_waiting_payment(True)

    def add_transaction(self, article_uid, article_price=1, is_dossier_structure=False):
        """ """
        if not self.is_manager():
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
            account_bills = self.get_account_bills()
            account_bills[-1]['payment_date'] = now
            self.set_account_bills(account_bills)
            self.set_payment_notification_date(None)
            self.set_expiration_notification_date(None)
            self.set_has_bill_waiting_payment(False)
            return True
        return False

    @staticmethod
    def _bill_waiting_payment(account_bills):
        ''' '''
        if len(account_bills) > 0:
            item = account_bills[-1]
            if item['payment_date'] is None and \
               item['date'] is not None and \
               item['mode'] == 'F':
                return item
        return None

    def get_bill_waiting_payment(self):
        '''
          Returns bill_id of the bill waiting for a payment
          Returns None if no bill is waiting for payment
        '''
        return CedesMemberData._bill_waiting_payment(self.get_account_bills())

    def _compute_payment_dates(self, formatted=False):
        """ """
        last_payment_date = self.get_last_payment_date(
            self.get_account_bills())
        expiration_date = self.get_expiration_date(last_payment_date)
        if formatted:
            ploneview = api.portal.get().unrestrictedTraverse('@@plone')
            return ploneview.toLocalizedTime(last_payment_date), \
                ploneview.toLocalizedTime(expiration_date),
        return last_payment_date, expiration_date

    @staticmethod
    def get_last_payment_date(account_bills):
        '''
          Returns the Date of the last time the account payment was validated.
          Returns None if the account was never credited
        '''
        if account_bills:
            bill_reversed = tuple(reversed(account_bills))
            for item in bill_reversed:
                if item['payment_date'] is not None and item['mode'] == "F":
                    return item['payment_date']
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

    def get_payment_notification_date(self):
        """ """
        return deepcopy(self.getProperty('payment_notification_date'))

    def set_payment_notification_date(self, date=None):
        """ """
        self.setMemberProperties({'payment_notification_date': date})

    def get_expiration_notification_date(self):
        """ """
        return deepcopy(self.getProperty('expiration_notification_date'))

    def set_expiration_notification_date(self, date=None):
        """ """
        self.setMemberProperties({'expiration_notification_date': date})

    def get_no_login_notification_date(self):
        """ """
        return deepcopy(self.getProperty('no_login_notification_date'))

    def set_no_login_notification_date(self, date=None):
        """ """
        self.setMemberProperties({'no_login_notification_date': date})

    def remove_failed_accounting(self):
        """ """
        self.setMemberProperties({'bill_accounting_failed': (),
                                  'has_failed_accounting_f': False,
                                  'has_failed_accounting_n': False,
                                  'has_bill_waiting_payment': False})

    def fix_failed_accounting(self, bill_id):
        '''
          Fix a failed accounting, turn the failed bill into a correct bill
          with a special id 'no_bill_id_failed_accounting_managed_manually'.
        '''
        bill_accounting_failed = self.get_bill_accounting_failed()
        if bill_accounting_failed is not None:
            if not bill_id:
                bill_id = 'no_bill_id_failed_accounting_managed_manually'
            self.add_bill(bill_id,
                          bill_accounting_failed[0],
                          bill_accounting_failed[1],
                          bill_accounting_failed[2], )
            self.setMemberProperties({'bill_accounting_failed': (),
                                      'has_failed_accounting_f': False,
                                      'has_failed_accounting_n': False,
                                      'has_bill_waiting_payment': False})

    def send_low_reminder(self):
        """ """
        send_mail("CeDES - Le solde de votre compte est bientôt épuisé",
                  template_name='mail_credit_low_notification',
                  options={'title': self.Title(),
                           'balance': self.get_account_balance(), },
                  mto=self.get_email())
        return True

    def send_credit_request_confirmation(self):
        """ """
        send_mail("CeDES - Votre demande de crédits a été acceptée",
                  template_name='mail_credit_request_confirmation',
                  options={'title': self.Title()},
                  mto=self.get_email())
        return True

    def send_100pc_confirmation(self):
        '''
          Sends an email to confirm Cedes100pc request accepted
          Returns True if email has been sent
        '''
        send_mail("CeDES - Votre demande d'abonnement à CeDES 100% a été acceptée",
                  template_name='mail_cedes100pc_request_confirmation',
                  options={'title': self.Title()},
                  mto=self.get_email())
        return True

    def send_no_login_notification(self, now, days=3):
        '''
          Sends an email to notify the user that he has never logged in after 3 days
          Returns True if email was sent
        '''
        # dont send notification if we have already send it within last d days
        # if a user has never logged in, the login time is set to 2000/01/01
        # the no_login_notification_date is set to 1950/01/01 by default
        no_login_notification_date = self.get_no_login_notification_date()
        if no_login_notification_date.year() == 1950 and \
           deepcopy(self.getProperty('last_login_time', '')).year() == 2000:
            registration_date = self.get_registration_date()
            # sends an email p_days after registration
            if registration_date + days < now:
                send_mail("CeDES - Votre inscription au site cedes",
                          template_name='mail_registration_nologin_notification',
                          options={'title': self.Title()},
                          mto=self.get_email())
                # marks member that notification has been sent
                self.set_no_login_notification_date(now)
                return True
        return False

    def reset_credit(self):
        '''Sets the balance to zero and adds the transaction information'''
        account_transactions = self.get_account_transactions()
        account_transactions = account_transactions + (
            ('expiration du crédit', self.get_account_balance(), DateTime()),)
        self.set_account_balance(0)

    def send_expiration_reminder(self, now, days=14):
        '''
          Sends expiration email reminder if credit expires in 14 days
          Returns True if email sent, False otherwise
        '''
        if not self.is_cedes_free() and not self.is_manager():
            last_payment_date = self.get_last_payment_date(self.get_account_bills())
            expiration_date = self.get_expiration_date(last_payment_date)
            # sends an email d days before only if the credits are not already expired!!!
            if expiration_date and expiration_date - days < now and not expiration_date < now:
                # dont send notification if we have already send it within last d days
                expiration_notification_date = self.get_expiration_notification_date()
                # the expiration_notification_date is set to 1950/01/01 by default
                if expiration_notification_date.year() == 1950:
                    # send a mail to the member to warn him...
                    last_payment_date, expiration_date = self._compute_payment_dates(formatted=True)
                    send_mail("CeDES - Vos crédits expirent bientôt",
                              template_name='mail_credit_expiration_notification',
                              options={'title': self.Title(),
                                       'expiration_date': expiration_date},
                              mto=self.get_email())
                    self.set_expiration_notification_date(now)
                    return True
        return False

    def reset_expired_credit(self, now):
        '''
          Reset credit of member if it has expired
          Returns 2 if credit was reset, 1 if credits reset and member set to "CeDES Free" and 0 if nothing is done...
        '''
        if not self.is_cedes_free() and not self.is_manager():
            last_payment_date = self.get_last_payment_date(self.get_account_bills())
            if last_payment_date and self.get_expiration_date(last_payment_date) < now:
                self.reset_credit()
                # !!! set the member to Free if his credits have expired and no bill is waiting payment !!!
                if not self.get_bill_waiting_payment():
                    self.set_member_type("CeDES Free")
                    # send a mail to the member to warn him...
                    last_payment_date, expiration_date = self._compute_payment_dates(formatted=True)
                    send_mail("CeDES - Vos crédits sont expirés",
                              template_name='mail_credit_expired_notification',
                              options={'title': self.Title(),
                                       'expiration_date': expiration_date},
                              mto=self.get_email())
                    return 1
                return 2
        return 0

    def send_payment_reminder(self, now, days=10):
        '''
          Sends a payment reminder email if payment has not been made last 10 days
          Returns True if email sent, False if there was an error getting the bill
          in the accounting application or None if nothing to do
        '''
        if not self.is_cedes_free() and not self.is_manager():
            bill_waiting_payment = self.get_bill_waiting_payment()
            if bill_waiting_payment:
                waiting_payment_date = bill_waiting_payment['date']
                # sends an email p_days after
                if now > waiting_payment_date + days:
                    # dont send notification if we have already sent
                    # the payment_notification_date is set to 1950/01/01 by default
                    payment_notification_date = self.get_payment_notification_date()
                    if payment_notification_date.year() == 1950:
                        # sends email with bill duplicata as attachment
                        bill = bill_waiting_payment.get('pdf', None)
                        if not bill:
                            return False
                        attachment = create_attachment('application/pdf', bill, 'facture.pdf')
                        send_mail(subject='CeDES - Votre paiement en attente',
                                  template_name='mail_credit_payment_notification',
                                  options={'title': self.Title()},
                                  mto=self.get_email(),
                                  attachments=[attachment])
                        # marks member that notification has been sent
                        self.set_payment_notification_date(now)
                        return True
        return None

    def retry_bill_credits(self):
        '''
          Tries to rebill credits if previous attempt failed
          Returns True if successfull, False otherwise
          None if member was not waiting to send a bill
        '''
        bill_accounting_failed = self.get_bill_accounting_failed()
        if bill_accounting_failed:
            return self.bill_credits(total=bill_accounting_failed[0], mode=bill_accounting_failed[1])
        else:
            return None

    def cancel_100_pc(self, now, days=30):
        '''
          Switch member to cedes free if never paid 30 days later, and his balance is 0
          deletes the payment_notification_date variable
          Sends a credit note to accounting
          Returns True if credit note was sent, False otherwise
        '''
        if not self.is_cedes_free() and not self.is_manager():
            bill_waiting_payment = self.get_bill_waiting_payment()
            if bill_waiting_payment:
                waiting_payment_date = bill_waiting_payment['date']
                if now > waiting_payment_date + days:
                    # set member to free only if his balance is zero
                    if self.get_account_balance() <= 0:
                        self.set_member_type("CeDES Free")
                    self.set_payment_notification_date(None)
                    # if len(self.account_bills)>0:
                    #   last_bill = self.account_bills[-1]
                    self.bill_credits(total=bill_waiting_payment['price'], mode="N")
                    return True
        return False
