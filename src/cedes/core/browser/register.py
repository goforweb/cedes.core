# -*- coding: utf-8 -*-

from cedes.core.memberdata import ICeDESUserDataSchema
from cedes.core.utils import add_page_message
from plone import api
from plone.app.users import schema as pau_schema
from plone.app.users.browser.account import AccountPanelSchemaAdapter
from plone.app.users.browser.register import RegistrationForm
from plone.app.users.browser.schemaeditor import getFromBaseSchema
from plone.autoform import directives
from Products.CMFPlone import PloneMessageFactory as _
from Products.CMFPlone.interfaces import IPloneSiteRoot
from Products.CMFPlone.utils import get_portal
from z3c.form.contentprovider import ContentProviders
from z3c.form.interfaces import HIDDEN_MODE
from z3c.form.interfaces import IFieldsAndContentProvidersForm
from zope import schema
from zope.component import provideAdapter
from zope.contentprovider.provider import ContentProviderBase
from zope.interface import implementer
from zope.interface import Invalid


class BillLabelProvider(ContentProviderBase):
    """ """

    def __init__(self, context, request, view):
        super(BillLabelProvider, self).__init__(context, request, view)
        self.__parent__ = view

    def render(self):
        if self.__parent__.form.widgets['bill_email'].mode != HIDDEN_MODE:
            return '<h3>Facturation</h3>'


def compute_constraint(value):
    """Must be 12."""
    if value != 12:
        raise Invalid('Veuillez corriger.')
    return True


def extra_field_constraint(value):
    """Must be empty."""
    if value:
        raise Invalid('Veuillez corriger.')
    return True


class ICeDESCombinedRegisterSchema(pau_schema.IRegisterSchema, ICeDESUserDataSchema):
    """ """
    # redefine member_type, we will hide it but it must be editable
    # and by default it is protected by the "Manage portal" permission
    directives.write_permission(member_type="cmf.AddPortalMember")
    member_type = schema.Choice(
        title=_(u'label_member_type', default=u'Member type'),
        values=['CeDES Free', 'CeDES 100%', '_no_set_'],
        default='_no_set_',
        required=True)

    # add extra fields to fight against robots
    compute = schema.Int(
        title=_('label_compute', default='Combien font trois fois quatre?'),
        description="Ceci nous permet de vérifier que vous n'êtes pas un robot",
        constraint=compute_constraint,
        required=True)
    # will be hidden using CSS
    extra_field = schema.TextLine(
        title=_('label_extra_field', default='Extra field'),
        constraint=compute_constraint,
        required=False)


@implementer(IFieldsAndContentProvidersForm)
class CeDESRegistrationForm(RegistrationForm):
    """ """
    contentProviders = ContentProviders()
    contentProviders['bill_label'] = BillLabelProvider
    contentProviders['bill_label'].position = 12

    @property
    def schema(self):
        """Copy of plone.app.users.browser.register.getRegisterSchema
           but use ICeDESCombinedRegisterSchema as base."""
        portal = get_portal()
        schema = getattr(portal, '_v_register_schema', None)
        if schema is None:
            portal._v_register_schema = schema = getFromBaseSchema(
                ICeDESCombinedRegisterSchema,
                form_name=u'On Registration'
            )
            # as schema is a generated supermodel,
            # needed adapters can only be registered at run time
            provideAdapter(AccountPanelSchemaAdapter, (IPloneSiteRoot,), schema)
        return schema

    def render(self):
        """Manage different registered page depending on member_type (Free/100%)."""
        if self._finishedRegister:
            portal_url = api.portal.get().absolute_url()
            url = "{0}/@@registered?member_type={1}".format(
                portal_url, self.widgets['member_type'].value[0])
            return self.request.RESPONSE.redirect(url)

        return super(CeDESRegistrationForm, self).render()

    def updateWidgets(self):
        """Hide "member_type" during registration."""

        super(CeDESRegistrationForm, self).updateWidgets()
        # manage creation of Free member, form is called with ?type=free
        # only set if _no_set_ default value is set
        # this handles form validation failure
        if self.widgets['member_type'].value == ["_no_set_"]:
            if self.request.form.get('type', None) == "free":
                self.widgets['member_type'].value = ["CeDES Free"]
            else:
                self.widgets['member_type'].value = ["CeDES 100%"]
        self.widgets['member_type'].mode = HIDDEN_MODE
        self.label = "Formulaire d'inscription - {0}".format(
            self.widgets['member_type'].value[0])

        # if member_type is "Free", hide the bill_* fields
        if self.widgets['member_type'].value == ["CeDES Free"]:
            for w in self.widgets:
                if w.startswith('bill'):
                    self.widgets[w].mode = HIDDEN_MODE
                    self.widgets[w].required = False

        # display a message explaining what will happen
        if self.widgets['member_type'].value == ["CeDES Free"]:
            add_page_message(self.context, 'inscription-avertissement-cedesfree')
        else:
            add_page_message(self.context, 'inscription-avertissement-cedes100pc')
