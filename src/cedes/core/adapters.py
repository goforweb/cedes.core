# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 by GoForWeb.be
#
# GNU General Public License (GPL)
#

from eea.facetednavigation.criteria.handler import Criteria as eeaCriteria
from plone.memoize import ram


class ThemeCriteria(eeaCriteria):
    """
      Criteria for Theme, use criteria stored on root (PlanClassement).
    """

    def compute_criteria_cachekey(method, self, context):
        '''cachekey method for self.compute_criteria.'''
        return context, str(context.REQUEST._debug)

    def __init__(self, context):
        """ """
        self.criteria = self.compute_criteria(context)

    @ram.cache(compute_criteria_cachekey)
    def compute_criteria(self, context):
        """ """
        root = context
        if not context.is_root():
            root = context.get_root_theme()
        self.context = root
        return self._criteria()
