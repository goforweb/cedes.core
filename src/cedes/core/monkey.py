# -*- coding: utf-8 -*-

from AuthEncoding import AuthEncoding
from cedes.core import logger
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

    # XXX cedes.core begin changes old password, check and add a message
    import hashlib
    import hmac
    key = b'<CedesMember at %s>' % login.encode()
    hmac_sha = hmac.new(key, password, hashlib.sha1).hexdigest()
    if reference == b'hmac_sha:' + hmac_sha.encode():
        from plone import api
        portal_url = api.portal.get().absolute_url()
        api.portal.show_message(
            "Vous utilisez un vieux mot de passe, veuillez le mettre à jour!\n"
            "Allez ci-dessus dans <a href='%s/my-account'>\"Mon compte\"</a> puis \"Définir un "
            "nouveau mot de passe\"." % portal_url,
            request=self.REQUEST,
            type="warning")
        return userid, login
    # ### cedes.core end changes

    return None


ZODBUserManager.authenticateCredentials = authenticateCredentials
logger.info("Monkey Products.PluggableAuthService.plugins.ZODBUserManager (authenticateCredentials)")
