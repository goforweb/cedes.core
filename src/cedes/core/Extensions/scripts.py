
from datetime import datetime
from plone import api


def update_account_transactions(self):
    """ """
    mutable_properties = self.acl_users.mutable_properties
    user_ids = []
    for k, v in mutable_properties._storage.items():
        user_ids.append(k) if not mutable_properties._storage[k]['isGroup'] else None
    for user_id in user_ids:
        user = api.user.get(user_id)
        user.set_account_transactions(
            tuple((tr[0], tr[1], datetime.now())
                for tr in user.get_account_transactions()))
