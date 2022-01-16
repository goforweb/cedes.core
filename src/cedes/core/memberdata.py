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

    def get_account_transactions(self):
        """ """
        return {}

    def get_first_login_time(self):
        """ """
        return datetime.now()

    def get_balance(self):
        """ """
        if "Manager" in self.getRoles():
            return 1000
        return 0

    def is_cedes_free(self):
        """ """
        return False

    def add_transaction(self, article_uid, article_price=1, id_dossier_structure=False):
        """ """
        if not("Manager" in self.getRoles()):
            # an article is payed once then accessed
            # but for DossierStructure, if it has been updated, the price is adapted and
            # the pdf is no more accessible
            if not id_dossier_structure and self.check_viewable(article_uid):
                return None
            previous_balance = self.get_balance()
            self.account_balance -= article_price
            if previous_balance >= 20 and self.account_balance < 20:
                self.send_low_reminder()
            self.account_transactions = self.account_transactions + \
                ((article_uid, article_price, datetime.now()), )
        return None

    def get_transactions(self):
        """ """
        return []

    def send_low_reminder(self):
        """ """
        # XXX
        return
        skintool = getToolByName(self, 'portal_skins')
        mailHost = getToolByName(self, 'MailHost')
        email = skintool.cedes_emails.credit_low_notification(
            self.REQUEST,
            fullname=self.fullname,
            firstname=self.firstname,
            member_email=self.email,
            balance=self.getBalance())
        mailHost.send(email.encode('utf-8'))
        return True
