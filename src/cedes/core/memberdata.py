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

    account_transactions = {}

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

    def check_viewable(self, article_uid):
        """
          Check if the article can still be viewed.
          An element is viewable when his UID is found in member transactions
        """
        res = "Manager" in self.getRoles()
        if not res:
            inversed_transactions = tuple(reversed(self.account_transactions))
            for tr_uid, tr_price, tr_date in inversed_transactions:
                if tr_uid == article_uid:
                    res = True
        return res

    def get_first_login_time(self):
        """ """
        return datetime.now()

    def get_balance(self):
        """ """
        return 0

    def is_cedes_free(self):
        """ """
        return False
