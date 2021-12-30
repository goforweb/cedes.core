# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 by GoForWeb.be
#
# GNU General Public License (GPL)
#

from datetime import datetime
from Products.PlonePAS.tools.memberdata import MemberData


class CedesMemberData(MemberData):
    """ """

    def check_balance(self, price):
        """
          Checks if we can afford a purchase's price
          Returns True if balance > price, False otherwise
        """
        if "Manager" in self.getRoles():
            return True
        if self.get_balance() - price >= 0:
            return True
        else:
            return False

    def get_first_login_time(self):
        """ """
        return datetime.now()

    def get_balance(self):
        """ """
        return 0

    def is_cedes_free(self):
        """ """
        return False
