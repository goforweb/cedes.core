# -*- coding: utf-8 -*-

from AccessControl import Unauthorized
from plone import api
from plone.app.users.browser.userdatapanel import UserDataPanel
from Products.Five import BrowserView
from z3c.form import field
from z3c.form import form
from z3c.form.interfaces import DISPLAY_MODE
from z3c.form.interfaces import HIDDEN_MODE
from zope import interface
from zope import schema
from zope.globalrequest import getRequest
from z3c.form import button
from DateTime import DateTime
from plone.protect import CheckAuthenticator


class AccountDetailsView(BrowserView):
    """ """

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.portal = api.portal.get()
        self.portal_url = self.portal.absolute_url()

    def _update(self):
        self.catalog = self.portal.portal_catalog
        self.member = self.portal.portal_membership.getMemberById(self.request.get('userid'))
        self.plone_view = self.portal.unrestrictedTraverse('@@plone')

    def __call__(self):
        """ """
        self._update()
        return super(AccountDetailsView, self).__call__()


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
        if not member.has_role("Manager"):
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
        # XXX manipulate self.fields BEFORE doing form.Form.updateWidgets
        self.fields['member_id'].mode = HIDDEN_MODE
        self.fields['member_type'].mode = DISPLAY_MODE
        self.fields['account_balance'].mode = DISPLAY_MODE
        form.Form.updateWidgets(self)

    def render(self):
        if self._redirect_to:
            self.request.response.redirect(self._redirect_to)
            return ""
        return super(MemberCreditForm, self).render()

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
            'Le compte de {0} ({1}) a été crédité de {2} points.'.format(
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


class RenewAccountForm(UserDataPanel):
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
            title = "Renouveller l'abonnement de {0} ({1})".format(
                self.member.getProperty('fullname'), self.member.getId())
        else:
            # editing my own profile
            title = "Renouvelle mon abonnement"

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
        return self.request.RESPONSE.redirect(api.portal.get().absolute_url())
