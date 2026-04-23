def _res_for_user(self, user):
        partner = user.partner_id
        if user == self.users[0]:
            return {
                "id": user.id,
                "employee_ids": user.employee_ids.ids,
                "partner_id": partner.id,
                "share": False,
            }
        if user == self.users[1]:
            return {
                "id": user.id,
                "partner_id": partner.id,
                "share": False,
            }
        if user == self.users[2]:
            return {
                "id": user.id,
                "employee_ids": user.employee_ids.ids,
                "partner_id": partner.id,
                "share": False,
            }
        if user == self.users[3]:
            return {
                "id": user.id,
                "employee_ids": user.employee_ids.ids,
                "partner_id": partner.id,
                "share": False,
            }
        if user == self.users[12]:
            return {
                "id": user.id,
                "employee_ids": user.employee_ids.ids,
                "partner_id": partner.id,
                "share": False,
            }
        if user == self.users[14]:
            return {
                "id": user.id,
                "employee_ids": user.employee_ids.ids,
                "partner_id": partner.id,
                "share": False,
            }
        if user == self.users[15]:
            return {
                "id": user.id,
                "employee_ids": user.employee_ids.ids,
                "partner_id": partner.id,
                "share": False,
            }
        if user == self.user_root:
            return {
                "id": user.id,
                "partner_id": partner.id,
                "share": False,
            }
        return {}