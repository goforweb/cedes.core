# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 by GoForWeb.be
#
# GNU General Public License (GPL)
#

from zope.i18n.locales import locales
from zope.i18n.locales.xmlfactory import LocaleFactory

import logging
import os


logger = logging.getLogger('cedes.core')

# use fr_patched.xml to have the entire year in short formatted date, so 01/01/20 will be 01/01/2020
locales._locales["fr", None, None] = LocaleFactory(
    os.path.join(os.path.dirname(__file__), "fr_patched.xml")
)()


def initialize(context):
    """ """
