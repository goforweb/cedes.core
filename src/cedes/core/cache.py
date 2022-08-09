# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 by GoForWeb.be
#
# GNU General Public License (GPL)
#

from datetime import datetime
from datetime import timedelta
from persistent.mapping import PersistentMapping
from plone import api
from plone.i18n.normalizer import IIDNormalizer
from plone.memoize.forever import _memos
from plone.memoize.interfaces import ICacheChooser
from zope.component import getUtility
from zope.component import queryUtility


VOLATILE_NAME_MAX_LENGTH = 200
VOLATILE_ATTR = '_volatile_cache_keys'
METHODS_MAPPING_NAME = '_methods_invalidation_mapping'


def cleanRamCache():
    """Clean the entire ram.cache."""
    cache_chooser = getUtility(ICacheChooser)
    thecache = cache_chooser('')
    thecache.ramcache.invalidateAll()


def cleanRamCacheFor(methodId):
    """Clean ram.cache for given p_methodId."""
    cache_chooser = getUtility(ICacheChooser)
    thecache = cache_chooser(methodId)
    thecache.ramcache.invalidate(methodId)


def cleanForeverCache():
    """Clean cache using the @forever.memoize decorator."""
    _memos.clear()


def get_cachekey_volatile(name, method=None, ttl=0):
    """Helper for using a volatile corresponding to p_name
       to be used as cachekey stored in a volatile.
       If it exists, we return the value, either we store datetime.now().
       If p_ttl (time to live) is given, a cachekey older that ttl is updated."""
    portal = api.portal.get()
    # use max_length of VOLATILE_NAME_MAX_LENGTH to avoid cropped names
    # that could lead to having 2 names beginning with same part using same volatile...
    normalized_name = queryUtility(IIDNormalizer).normalize(
        name, max_length=VOLATILE_NAME_MAX_LENGTH)
    volatile_name = normalized_name
    volatiles = getattr(portal, VOLATILE_ATTR, None)
    if volatiles is None:
        portal._volatile_cache_keys = PersistentMapping()
        volatiles = portal._volatile_cache_keys
    date = volatiles.get(volatile_name)
    now = datetime.now()
    # compute new date if None or if using ttl and ttl is stale
    if not date or (ttl and date + timedelta(seconds=ttl) < now):
        date = now
        volatiles[volatile_name] = date
    # store caller method path so it will be invalidated in invalidate_cachekey_volatile_for
    if method:
        key = '%s.%s' % (method.__module__, method.__name__)
        methods = volatiles.get(METHODS_MAPPING_NAME)
        if methods is None:
            volatiles[METHODS_MAPPING_NAME] = PersistentMapping()
        if name not in volatiles[METHODS_MAPPING_NAME]:
            volatiles[METHODS_MAPPING_NAME][name] = []
        if key not in volatiles[METHODS_MAPPING_NAME][name]:
            volatiles[METHODS_MAPPING_NAME][name].append(key)
    return date


def invalidate_cachekey_volatile_for(name, get_again=False, invalidate_cache=True):
    """ """
    portal = api.portal.get()
    normalized_name = queryUtility(IIDNormalizer).normalize(
        name, max_length=VOLATILE_NAME_MAX_LENGTH)
    volatile_name = normalized_name
    volatiles = getattr(portal, VOLATILE_ATTR, {})
    if volatile_name in volatiles:
        del volatiles[volatile_name]
    # when the key is invalidated, get_cachekey_volatile so it
    # stores a new date and it avoids a second write
    if get_again:
        get_cachekey_volatile(volatile_name)
    # when date is invalidated, every cache using it is stale
    # so we may either specifically invalidate this cached methods
    # or just wait for ram.cache to do it's cleanup itself
    if invalidate_cache:
        mapping = volatiles.get(METHODS_MAPPING_NAME, {})
        if name in mapping:
            for method in mapping[name]:
                cleanRamCacheFor(method)
            mapping.pop(name)
