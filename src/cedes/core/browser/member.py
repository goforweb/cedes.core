# -*- coding: utf-8 -*-

from AccessControl import Unauthorized
from cedes.core.browser.overrides import CeDESUserDataPanel
from cedes.core.utils import add_page_message
from cedes.core.utils import create_attachment
from cedes.core.utils import get_member
from cedes.core.utils import send_mail
from collections import OrderedDict
from DateTime import DateTime
from io import BytesIO
from plone import api
from plone.autoform import directives
from plone.autoform.form import AutoExtensibleForm
from plone.namedfile.field import NamedFile
from plone.protect import CheckAuthenticator
from plone.supermodel import model
from plone.z3cform.layout import wrap_form
from Products.CMFPlone import PloneMessageFactory as _
from Products.CMFPlone.utils import safe_unicode
from Products.Five import BrowserView
from PyPDF2.pdf import PdfFileReader
from z3c.form import button
from z3c.form import field
from z3c.form import form
from z3c.form.form import EditForm
from z3c.form.interfaces import DISPLAY_MODE
from z3c.form.interfaces import HIDDEN_MODE
from zope import interface
from zope import schema
from zope.globalrequest import getRequest

import mimetypes
import z3c.form.button


class AccountDetailsView(BrowserView):
    """ """

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.portal = api.portal.get()
        self.portal_url = self.portal.absolute_url()

    def _update(self):
        self.catalog = self.portal.portal_catalog
        self.member = get_member(self.request)
        self.plone_view = self.portal.unrestrictedTraverse('@@plone')

    def download_bill_url(self):
        """ """
        url = "{0}/@@download-bill-waiting-payment".format(self.portal_url)
        if api.user.get_current().is_manager():
            url += "?userid={0}".format(self.member.getId())
        return url

    def __call__(self):
        """ """
        self._update()
        return super(AccountDetailsView, self).__call__()


class MyAccountView(AccountDetailsView):
    """ """

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.portal = api.portal.get()
        self.portal_url = self.portal.absolute_url()

    def _update(self):
        self.catalog = self.portal.portal_catalog
        self.member = get_member(self.request)
        self.last_payment_date, self.expiration_date = self.member._compute_payment_dates()
        self.plone_view = self.portal.unrestrictedTraverse('@@plone')

    def __call__(self):
        """ """
        self._update()
        return super(MyAccountView, self).__call__()


class MemberDebugView(BrowserView):
    """ """

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.portal = api.portal.get()
        self.portal_url = self.portal.absolute_url()

    def _update(self):
        self.catalog = self.portal.portal_catalog
        self.member = get_member(self.request)
        self.plone_view = self.portal.unrestrictedTraverse('@@plone')

    def __call__(self):
        """ """
        self._update()
        # member properties
        self.data = OrderedDict()
        properties_storage = self.portal.acl_users.mutable_properties._storage
        self.data = sorted(properties_storage.get(self.member.getId()).items())
        # some extra computed data
        self.computed = OrderedDict()
        # add bill_waiting_payment but remove pdf data for display
        bill_waiting_payment = self.member.get_bill_waiting_payment()
        if bill_waiting_payment and 'pdf' in bill_waiting_payment:
            bill_waiting_payment.pop('pdf')
        self.computed['bill_waiting_payment'] = bill_waiting_payment
        self.computed['last_payment_date'], self.computed['expiration_date'] = \
            self.member._compute_payment_dates()
        # check if a password reset is on the way
        pw_reset = api.portal.get_tool('portal_password_reset')
        self.computed['pw_reset'] = None
        pw_reset_data = {infos[1]: randomstring for randomstring, infos in pw_reset._requests.items()
                         if infos[0] == self.member.getId()}
        if pw_reset_data:
            randomstring = pw_reset_data[max(pw_reset_data.keys())]
            self.computed['pw_reset'] = \
                "{0} (<a href='{1}/passwordreset/{2}?userid={3}'>User reset pw link</a>)".format(
                    max(pw_reset_data).strftime('%Y/%m/%d %H:%M'),
                    self.portal_url,
                    randomstring,
                    self.member.getUserName())
        # sorte computed data
        self.computed = sorted(self.computed.items())
        return super(MemberDebugView, self).__call__()


class DownloadBillWaitingPayment(BrowserView):
    """ """

    def _update(self):
        self.member = get_member(self.request)

    def __call__(self):
        ''' '''
        self._update()
        bill = self.member.get_bill_waiting_payment()
        pdf = bill.get('pdf', None)
        if pdf:
            self._set_header_response('facture.pdf')
            return pdf

    def _set_header_response(self, filename):
        """
        Tell the browser that the resulting page contains ODT.
        """
        response = self.request.RESPONSE
        mimetype = mimetypes.guess_type(filename)[0]
        response.setHeader('Content-type', mimetype)
        response.setHeader(
            'Content-disposition',
            u'inline;filename="{}"'.format(filename).encode('utf-8'))


def member_id_default():
    """
      Get the value from the REQUEST as it is passed when calling the
      form : form?userid=member_user_id.
    """
    req = getRequest()
    return req.get('userid', req.form.get('form.widgets.member_id'))


def member_type_default():
    """ """
    member_id = member_id_default()
    member = api.user.get(member_id)
    return member.get_member_type()


def account_balance_default():
    """ """
    member_id = member_id_default()
    member = api.user.get(member_id)
    return member.get_account_balance()


class IMemberCredit(interface.Interface):
    """ """

    member_id = schema.TextLine(
        title="Member id",
        defaultFactory=member_id_default,
        required=False)

    member_type = schema.Choice(
        title="Type d'abonnement",
        values=['CeDES Free', 'CeDES 100%'],
        defaultFactory=member_type_default,
        required=True)

    account_balance = schema.Int(
        title="Solde actuel",
        defaultFactory=account_balance_default)

    credit = schema.Int(
        title="Crédit le compte de (points)",
        default=0)


class MemberCreditForm(form.Form):
    """ """

    fields = field.Fields(IMemberCredit)
    ignoreContext = True  # don't use context to get widget data

    # put the 'gopress' in first position
    label = "Créditer le compte de {0} ({1})"
    description = ''
    _redirect_to = ''

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.portal = api.portal.get()

    def _check_auth(self):
        """Raise Unauthorized if current user can use form."""
        member = api.user.get_current()
        if not member.is_manager():
            raise Unauthorized

    @property
    def _member(self):
        """ """
        member = getattr(self, "_cache_member", None)
        if member is None:
            member = api.user.get(self.widgets['member_id'].value)
            setattr(self, "_cache_member", member)
        return member

    def update(self):
        """ """
        self._check_auth()
        super(MemberCreditForm, self).update()
        # update label
        self.label = self.label.format(
            self._member.getProperty('fullname'), self._member.getId())
        # after calling parent's update, self.actions are available
        # show relevant buttons and adapt description
        # excepted if action was already executed
        if not self.actions.executedActions:
            if self._member.is_cedes_free():
                self.description = "Si vous créditez ce membre Free gratuitement, il " \
                    "passera en mode CeDES 100% sans émission de facture et ses crédits " \
                    "auront une validité de un an"
                self.actions.get('credit_free').addClass('btn-primary')
            else:
                self.description = ""
                self.actions.get('credit').addClass('btn-primary')
                self.actions.get('credit_and_validate_payment').addClass('btn-primary')

    def updateWidgets(self):
        # manipulate self.fields BEFORE doing form.Form.updateWidgets
        self.fields['member_id'].mode = HIDDEN_MODE
        self.fields['member_type'].mode = DISPLAY_MODE
        self.fields['account_balance'].mode = DISPLAY_MODE
        form.Form.updateWidgets(self)

    def render(self):
        if self._redirect_to:
            self.request.response.redirect(self._redirect_to)
            return ""
        return super(MemberCreditForm, self).render()

    @button.buttonAndHandler('Créditer et valider le paiement',
                             name='credit_and_validate_payment',
                             condition=lambda form: not form._member.is_cedes_free())
    def handle_credit_and_validate_payment(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return
        self._do_credit_and_validate_payment(data)
        self._redirect_to = "{0}/@@member-search?form.widgets.login={1}" \
            "&form.widgets.member_type:list=&form.buttons.search=1".format(
                self.portal.Members.absolute_url(), data['member_id'])

    @button.buttonAndHandler('Créditer gratuitement',
                             name='credit',
                             condition=lambda form: not form._member.is_cedes_free())
    def handle_credit(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return
        self._do_credit(data)
        self._redirect_to = "{0}/@@member-search?form.widgets.login={1}" \
            "&form.widgets.member_type:list=&form.buttons.search=1".format(
                self.portal.Members.absolute_url(), data['member_id'])

    @button.buttonAndHandler('Créditer le membre CeDES Free gratuitement',
                             name='credit_free',
                             condition=lambda form: form._member.is_cedes_free())
    def handle_credit_free(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return
        self._do_credit_free(data)
        self._redirect_to = "{0}/@@member-search?form.widgets.login={1}" \
            "&form.widgets.member_type:list=&form.buttons.search=1".format(
                self.portal.Members.absolute_url(), data['member_id'])

    @button.buttonAndHandler("Annuler", name='cancel')
    def handle_cancel(self, action):
        self._redirect_to = self.portal.Members.absolute_url()

    def _do_credit(self, data):
        """ """
        member = self._member
        member.credit(data['credit'])
        self.portal.plone_utils.addPortalMessage(
            'Le compte de {0} ({1}) a été crédité de {2} points.'.format(
                member.getProperty('fullname'), member.getId(), str(data['credit'])))

    def _do_credit_and_validate_payment(self, data):
        """ """
        member = self._member
        member.credit(data['credit'])
        now = DateTime()
        member.validate_payment(now)
        self.portal.plone_utils.addPortalMessage(
            'Le compte de {0} ({1}) a été crédité de {2} points et la facture '
            'en attente de paiement a été validée.'.format(
                member.getProperty('fullname'), member.getId(), str(data['credit'])))

    def _do_credit_free(self, data):
        """ """
        member = self._member
        member.credit(data['credit'])
        now = DateTime()
        # add a fake payment
        member.add_bill('no_bill_id_free_credits', price=0, mode='F', date=now, payment_date=None)
        # validate the fake payment
        member.validate_payment(now)
        # set the member to "CeDES 100%"
        member.set_member_type("CeDES 100%")
        self.portal.plone_utils.addPortalMessage(
            'Le compte de {0} ({1}) a été crédité de {2} points. Le membre est '
            'maintenant CeDES 100% et ses crédits ont une validité de un an.'.format(
                member.getProperty('fullname'), member.getId(), str(data['credit'])))


class RenewAccountForm(CeDESUserDataPanel):
    """ """

    form_name = "Renouveler mon abonnement"

    def prepareObjectTabs(self,
                          default_tab='view',
                          sort_first=['folderContents']):
        # hide other tabs
        # tabs = super(RenewAccountForm, self).prepareObjectTabs(default_tab, sort_first)
        # add the "member-renew" tab
        current_user_id = api.user.get_current().getId()
        if self.member.getId() != current_user_id:
            # editing someone else's profile
            title = "Renouveler l'abonnement de {0} ({1})".format(
                self.member.getProperty('fullname'), self.member.getId())
        else:
            # editing my own profile
            title = self.form_name

        navigation_root_url = self.context.absolute_url()
        tabs = []
        tabs.append({
            'title': title,
            'url': navigation_root_url + '/@@member-renew',
            'selected': (self.__name__ == 'member-renew'),
            'id': 'user_data-member-renew',
        })
        return tabs

    @property
    def description(self):
        return "Vérifiez vos données et cliquez sur \"Renouveler mon abonnement\" au bas du formulaire"

    def update(self):
        """ """
        super(RenewAccountForm, self).update()
        # make renew button primary
        self.actions.get('renew').addClass('btn-primary')
        # display a message explaining what will happen
        add_page_message(self.context, 'inscription-member-renew-100')

    @button.buttonAndHandler(u'Renouveler mon abonnement', name='renew')
    def handleRenew(self, action):
        CheckAuthenticator(self.request)
        data, errors = self.extractData()
        if action.form.widgets.errors:
            self.status = self.formErrorsMessage
            return

        # check again this even if it is checked in the template because a back
        # in the brower + send info again could request credits again...
        if not self.member.get_bill_waiting_payment():
            self.member.request_credit()
            api.portal.show_message('Demande de renouvellement acceptée.', self.request)
        else:
            api.portal.show_message(
                'Vous avez déjà une facture en attente de paiement!', self.request, type='warning')
        return self.request.RESPONSE.redirect(self.context.absolute_url())

    @button.buttonAndHandler("Annuler", name='cancel')
    def handle_cancel(self, action):
        # redirect to user personal preferences
        api.portal.show_message('Demande de renouvellement annulée.', self.request)
        return self.request.RESPONSE.redirect(self.context.absolute_url() + '/@@my-account')


class Switch100Form(CeDESUserDataPanel):
    """ """

    form_name = "Devenir membre CeDES 100%"

    def _hide_bill_fields(self):
        """Member is switching to CeDES 100%, show bill fields."""
        return False

    def prepareObjectTabs(self,
                          default_tab='view',
                          sort_first=['folderContents']):
        # hide other tabs
        # tabs = super(Switch100Form, self).prepareObjectTabs(default_tab, sort_first)
        # add the "member-switch100" tab
        navigation_root_url = self.context.absolute_url()
        tabs = []
        tabs.append({
            'title': self.form_name,
            'url': navigation_root_url + '/@@member-switch100',
            'selected': (self.__name__ == 'member-switch100'),
            'id': 'user_data-member-switch100',
        })
        return tabs

    @property
    def description(self):
        return "Vérifiez vos données et cliquez sur \"Devenir membre 100%\" au bas du formulaire"

    def update(self):
        """ """
        super(Switch100Form, self).update()
        # make switch100 button primary
        self.actions.get('switch100').addClass('btn-primary')
        # display a message explaining what will happen
        add_page_message(self.context, 'inscription-member-switch-100')

    @button.buttonAndHandler(u'Devenir membre 100%', name='switch100')
    def handleSwitch100(self, action):
        CheckAuthenticator(self.request)
        data, errors = self.extractData()
        if action.form.widgets.errors:
            self.status = self.formErrorsMessage
            return

        # check again this even if it is checked in the template because a back
        # in the brower + send info again could request credits again...
        if not self.member.get_bill_waiting_payment():
            self.member.request_100pc()
            api.portal.show_message('Demande d\'abonnement acceptée.', self.request)
        else:
            api.portal.show_message(
                'Vous avez déjà une facture en attente de paiement!', self.request, type='warning')
        return self.request.RESPONSE.redirect(self.context.absolute_url())

    @button.buttonAndHandler("Annuler", name='cancel')
    def handle_cancel(self, action):
        # redirect to user personal preferences
        api.portal.show_message('Demande d\'abonnement annulée.', self.request)
        return self.request.RESPONSE.redirect(self.context.absolute_url() + '/@@my-account')


def came_from_default():
    """
    """
    request = getRequest()
    return safe_unicode(request.get('HTTP_REFERER', u''))


def accounting_mode_default():
    """
    """
    request = getRequest()
    return safe_unicode(request.get('accounting_mode', u'NoValidation'))


class IFixFailedAccountingSchema(model.Schema):

    member_id = schema.TextLine(
        title="Member id",
        defaultFactory=member_id_default,
        required=False)

    file = NamedFile(
        title=_(u'Facture/Note de crédit au format PDF'),
        description=u"Sélectionnez le fichier à envoyer, l'application "
                    u"détectera le type de fichier (Facture ou Note de Crédit) "
                    u"ainsi que la référence automatiquement")

    accounting_mode_validation = schema.Choice(
        title=u"Validation du type de fichier joint",
        description=u"Par défaut, laissez la valeur sélectionnée par l'application "
                    u"(\"F\" pour \"Facture\" et \"N\" pour \"Note de crédit\"), "
                    u"ceci vérifiera que le fichier PDF joint est correct. "
                    u"Si la validation ne passe pas, sélectionnez \"NoValidation\"",
        defaultFactory=accounting_mode_default,
        values=(u'NoValidation', u'F', u'N'),
        required=True,
    )

    bill_id = schema.TextLine(
        title=u"Référence",
        description=u"Par défaut, laissez ce champ vide, l'application extrairera "
                    u"la référence depuis le fichier PDF joint",
        required=False)

    directives.mode(came_from='hidden')
    came_from = schema.TextLine(
        title=u"came_from",
        defaultFactory=came_from_default,
        required=False)


class FixFailedAccountingForm(AutoExtensibleForm, EditForm):
    """
    """
    label = _(u'Gérer la facture/note de crédit échouée')
    schema = IFixFailedAccountingSchema
    ignoreContext = True

    @property
    def _member(self):
        """ """
        member = getattr(self, "_cache_member", None)
        if member is None:
            member = api.user.get(self.widgets['member_id'].value)
            setattr(self, "_cache_member", member)
        return member

    def update(self):
        """ """
        super(FixFailedAccountingForm, self).update()
        # make send button primary
        self.actions.get('send').addClass('btn-primary')

    def updateWidgets(self):
        # manipulate self.fields BEFORE doing form.Form.updateWidgets
        self.fields['member_id'].mode = HIDDEN_MODE
        form.Form.updateWidgets(self)
        self.member = self._member

    @z3c.form.button.buttonAndHandler(_(u'Send'), name='send')
    def fix_failed_accounting_and_send_bill(self, action):
        """ Create and handle form button
        """
        # Extract form field values and errors from HTTP request
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return

        # get data
        file_data = data['file'].data
        bill_id = data['bill_id']

        if data['accounting_mode_validation'] != 'NoValidation':
            try:
                file_accounting_mode = None
                file_accounting_mode = self._extract_accounting_mode_from_pdf(file_data)
            except Exception as exc:
                api.portal.show_message(
                    _(u"Error trying to extract accounting_mode from PDF file, "
                      u"raised error was {0}".format(exc)),
                    request=self.request, type="error")
        else:
            file_accounting_mode = 'NoValidation'

        if file_accounting_mode and file_accounting_mode != data['accounting_mode_validation']:
            file_accounting_mode = None
            api.portal.show_message(
                _(u"La validation du type de fichier joint a échoué!"),
                request=self.request, type="error")

        # fix failed accounting
        if file_accounting_mode and not bill_id:
            try:
                bill_id = self._extract_bill_id_from_pdf(file_data)
            except Exception as exc:
                api.portal.show_message(
                    _(u"Error trying to extract bill_id from PDF file, raised error was {0}".format(exc)),
                    request=self.request, type="error")
        # proceed only if accounting_mode and bill_id are valid
        if file_accounting_mode and bill_id:
            # send bill by email
            self._send_bill_email(file_data, file_accounting_mode)
            # store bill PDF file_data into last accounting infos
            self.member.fix_failed_accounting(bill_id=bill_id)
            account_bills = self.member.get_account_bills()
            account_bills[-1]['pdf'] = file_data
            self.member.set_account_bills(account_bills)

            if file_accounting_mode == 'F':
                api.portal.show_message(
                    _(u"La facture problématique de \"{0}\" a été annulée et un e-mail "
                      u"avec la facture en pièce jointe lui a été envoyé.  "
                      u"La référence utilisée est \"{1}\".".format(
                          self.member.Title(), bill_id)),
                    request=self.request)
            else:
                api.portal.show_message(
                    _(u"La facture en attente de paiement de \"{0}\" a été annulée et un e-mail "
                      u"avec la note de crédit en pièce jointe lui a été envoyé.  "
                      u"La référence utilisée est \"{1}\".".format(
                          self.member.Title(), bill_id)),
                    request=self.request)
        else:
            api.portal.show_message(
                _(u"Impossible d'extraire la référence ou le type de document depuis le fichier PDF... "
                  u"Le document n'a pas été envoyé, encodez un numéro de référence manuellement, "
                  u"choisissez un type de document (champ \"Validation du type de fichier joint\") "
                  u"et contactez votre administrateur système."),
                request=self.request, type="warning")
        # redirect to members search
        self.request.RESPONSE.redirect(data['came_from'])

    @z3c.form.button.buttonAndHandler(u'Enlever l\'état "Échoué" (annule sans envoi)',
                                      name='remove_failed_accounting')
    def remove_failed_accounting(self, action):
        """ Just remove the failed accounting marker
        """
        # Extract form field values and errors from HTTP request
        data, errors = self.extractData()
        self.member.remove_failed_accounting()
        api.portal.show_message(
            u"La facture problématique de \"{0}\" a été annulée sans envoi d'e-mail.".format(
                self.member.Title()),
            request=self.request)

        # redirect to members search
        self.request.RESPONSE.redirect(data['came_from'])

    @z3c.form.button.buttonAndHandler(_('Cancel'), name='cancel')
    def cancel(self, action):
        """ Create and handle form button
        """
        # Extract form field values and errors from HTTP request
        data, errors = self.extractData()
        self.request.RESPONSE.redirect(data['came_from'])
        api.portal.show_message(_(u'Action annulée.'), request=self.request)

    def _send_bill_email(self, bill, accounting_mode):
        """ """
        if accounting_mode == 'F':
            subject = '[CeDES] - Facture'
            template_name = 'mail_credit_bill_notification'
            options = {'title': self.member.Title()}
            filename = 'facture.pdf'
        else:
            # 'N'
            subject = '[CeDES] - Note de crédit'
            template_name = 'mail_credit_note_notification'
            ploneview = self.context.unrestrictedTraverse("@@plone")
            bill_date = ploneview.toLocalizedTime(
                self.member.get_bill_waiting_payment()['date'])
            options = {'title': self.member.Title(), 'bill_date': bill_date}
            filename = 'note_de_credit.pdf'
        attachment = create_attachment('application/pdf', bill, filename)
        send_mail(subject=subject,
                  template_name=template_name,
                  options=options,
                  mto=self.member.get_email(),
                  attachments=[attachment])

    def _extract_bill_id_from_pdf(self, pdf_data):
        """ """
        bill_id = None
        pdf_file = BytesIO(pdf_data)
        pdf = PdfFileReader(pdf_file)
        page = pdf.getPage(0)
        # make sure we do not get "\n" between "Date" and the begin of the
        # bill_id that starts with "VE..."
        text = page.extractText().replace("\n", "")
        start_index = text.find('DateV')
        if start_index != -1:
            # bypass 'Date' part
            start_index = start_index + 4
            bill_id = text[start_index:start_index + 10]
        return bill_id

    def _extract_accounting_mode_from_pdf(self, pdf_data):
        """ """
        accounting_mode = None
        pdf_file = BytesIO(pdf_data)
        pdf = PdfFileReader(pdf_file)
        page = pdf.getPage(0)
        text = page.extractText()
        start_index = text.find('Facture')
        if start_index != -1:
            accounting_mode = 'F'
        start_index = text.find('Note de crédit')
        if start_index != -1:
            accounting_mode = 'N'
        return accounting_mode


FixFailedAccountingFormWrapper = wrap_form(FixFailedAccountingForm)
