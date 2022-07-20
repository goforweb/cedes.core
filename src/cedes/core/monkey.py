# -*- coding: utf-8 -*-

from AuthEncoding import AuthEncoding
from cedes.core import logger
from eea.facetednavigation.widgets.sorting.widget import Widget
from plone.app.vocabularies.principals import PrincipalsVocabulary
from plone.memoize import ram
from Products.PlonePAS.tools.membership import MembershipTool
from Products.PluggableAuthService.plugins.ZODBUserManager import ZODBUserManager

import six


try:
    from hashlib import sha1 as sha
except ImportError:
    from sha import sha


ZODBUserManager.__old_authenticateCredentials = ZODBUserManager.authenticateCredentials


def authenticateCredentials(self, credentials):
    """ See IAuthenticationPlugin.

    o We expect the credentials to be those returned by
      ILoginPasswordExtractionPlugin.
    """
    login = credentials.get('login')
    password = credentials.get('password')

    if login is None or password is None:
        return None

    # Do we have a link between login and userid?  Do NOT fall
    # back to using the login as userid when there is no match, as
    # that gives a high chance of seeming to log in successfully,
    # but in reality failing.
    userid = self._login_to_userid.get(login)
    if userid is None:
        # Someone may be logging in with a userid instead of a
        # login name and the two are not the same.  We could try
        # turning those around, but really we should just fail.
        #
        # userid = login
        # login = self._userid_to_login.get(userid)
        # if login is None:
        #     return None
        return None

    reference = self._user_passwords.get(userid)

    if reference is None:
        return None

    if AuthEncoding.is_encrypted(reference):
        if AuthEncoding.pw_validate(reference, password):
            return userid, login

    # Support previous naive behavior
    if isinstance(password, six.text_type):
        password = password.encode('utf8')
    digested = sha(password).hexdigest()

    if reference == digested:
        return userid, login

    # XXX cedes.core begin changes old password, check and update if correct
    import hashlib
    import hmac
    key = b'<CedesMember at %s>' % login.encode()
    hmac_sha = hmac.new(key, password, hashlib.sha1).hexdigest()
    if reference == b'hmac_sha:' + hmac_sha.encode():
        # we have an old password, update it
        self._user_passwords[userid] = self._pw_encrypt(password)
        return userid, login
    # XXX cedes.core end changes

    return None


ZODBUserManager.authenticateCredentials = authenticateCredentials
logger.info("Monkey Products.PluggableAuthService.plugins.ZODBUserManager (authenticateCredentials)")


def getMemberInfo_cachekey(method, self, memberId=None):
    '''cachekey method for self.getMemberInfo.
       Cache is invalidated by plone.app.controlpanel upon any control panel changes.'''
    return memberId


MembershipTool.__old_getMemberInfo = MembershipTool.getMemberInfo


@ram.cache(getMemberInfo_cachekey)
def getMemberInfo(self, memberId=None):
    """Monkeypatched to add caching."""
    return self.__old_getMemberInfo(memberId)


MembershipTool.getMemberInfo = getMemberInfo
logger.info("Monkey patching Products.PlonePAS.tools.membership.MembershipTool (getMemberInfo)")


# Widget.listSortFields
def listSortFields_cachekey(method, self):
    '''cachekey method for self.listSortFields.'''
    return True


Widget.__old_listSortFields = Widget.listSortFields


@ram.cache(listSortFields_cachekey)
def listSortFields(self):
    """Monkeypatched to add caching."""
    # do not return a generator
    return [k for k in self.__old_listSortFields()]


Widget.listSortFields = listSortFields
logger.info("Monkey patching eea.facetednavigation.widgets.sorting.widget.Widget (listSortFields)")


# PrincipalsVocabulary._get_term_from_source
def _get_term_from_source_cachekey(method, self, value=None, token=None):
    '''cachekey method for self._get_term_from_source.'''
    return value, token


PrincipalsVocabulary.__old__get_term_from_source = PrincipalsVocabulary._get_term_from_source


@ram.cache(_get_term_from_source_cachekey)
def _get_term_from_source(self, value=None, token=None):
    """Monkeypatched to add caching."""
    # do not return a generator
    return self.__old__get_term_from_source(value, token)


PrincipalsVocabulary._get_term_from_source = _get_term_from_source
logger.info("Monkey patching plone.app.vocabularies.principals.PrincipalsVocabulary (_get_term_from_source)")
