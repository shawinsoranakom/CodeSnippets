def _expected_result_for_persona(
        self,
        user=None,
        guest=None,
        only_inviting=False,
        also_livechat=False,
        also_notification=False,
    ):
        if user == self.users[0]:
            res = {
                "active": True,
                "avatar_128_access_token": user.partner_id._get_avatar_128_access_token(),
                "email": "e.e@example.com",
                "id": user.partner_id.id,
                "im_status": "online",
                "im_status_access_token": user.partner_id._get_im_status_access_token(),
                "is_company": False,
                "main_user_id": user.id,
                "mention_token": user.partner_id._get_mention_token(),
                "name": "Ernest Employee",
                "write_date": fields.Datetime.to_string(user.partner_id.write_date),
            }
            if also_livechat:
                res.update(
                    {
                        "country_id": False,
                        "is_public": False,
                        "user_livechat_username": False,
                    }
                )
            if also_notification:
                res["name"] = "Ernest Employee"
            return res
        if user == self.users[1]:
            res = {
                "active": True,
                "avatar_128_access_token": user.partner_id._get_avatar_128_access_token(),
                "country_id": self.env.ref("base.in").id,
                "id": user.partner_id.id,
                "im_status": "offline",
                "im_status_access_token": user.partner_id._get_im_status_access_token(),
                "is_company": False,
                "is_public": False,
                "main_user_id": user.id,
                "name": "test1",
                "mention_token": user.partner_id._get_mention_token(),
                "write_date": fields.Datetime.to_string(user.partner_id.write_date),
            }
            if also_livechat:
                res["offline_since"] = False
                res["user_livechat_username"] = False
                res["email"] = user.email
            return res
        if user == self.users[2]:
            if only_inviting:
                return {
                    "avatar_128_access_token": user.partner_id._get_avatar_128_access_token(),
                    "id": user.partner_id.id,
                    "im_status": "offline",
                    "im_status_access_token": user.partner_id._get_im_status_access_token(),
                    "name": "test2",
                    "mention_token": user.partner_id._get_mention_token(),
                    "write_date": fields.Datetime.to_string(user.partner_id.write_date),
                }
            return {
                "active": True,
                "avatar_128_access_token": user.partner_id._get_avatar_128_access_token(),
                "email": "test2@example.com",
                "id": user.partner_id.id,
                "im_status": "offline",
                "im_status_access_token": user.partner_id._get_im_status_access_token(),
                "is_company": False,
                "main_user_id": user.id,
                "mention_token": user.partner_id._get_mention_token(),
                "name": "test2",
                "write_date": fields.Datetime.to_string(user.partner_id.write_date),
            }
        if user == self.users[3]:
            return {
                "active": True,
                "avatar_128_access_token": user.partner_id._get_avatar_128_access_token(),
                "email": False,
                "id": user.partner_id.id,
                "im_status": "offline",
                "im_status_access_token": user.partner_id._get_im_status_access_token(),
                "is_company": False,
                "main_user_id": user.id,
                "mention_token": user.partner_id._get_mention_token(),
                "name": "test3",
                "write_date": fields.Datetime.to_string(self.users[3].partner_id.write_date),
            }
        if user == self.users[12]:
            return {
                "active": True,
                "avatar_128_access_token": user.partner_id._get_avatar_128_access_token(),
                "email": False,
                "id": user.partner_id.id,
                "im_status": "offline",
                "im_status_access_token": user.partner_id._get_im_status_access_token(),
                "is_company": False,
                "main_user_id": user.id,
                "mention_token": user.partner_id._get_mention_token(),
                "name": "test12",
                "write_date": fields.Datetime.to_string(user.partner_id.write_date),
            }
        if user == self.users[14]:
            return {
                "active": True,
                "avatar_128_access_token": user.partner_id._get_avatar_128_access_token(),
                "email": False,
                "id": user.partner_id.id,
                "im_status": "offline",
                "im_status_access_token": user.partner_id._get_im_status_access_token(),
                "is_company": False,
                "main_user_id": user.id,
                "mention_token": user.partner_id._get_mention_token(),
                "name": "test14",
                "write_date": fields.Datetime.to_string(user.partner_id.write_date),
            }
        if user == self.users[15]:
            return {
                "active": True,
                "avatar_128_access_token": user.partner_id._get_avatar_128_access_token(),
                "email": False,
                "id": user.partner_id.id,
                "im_status": "offline",
                "im_status_access_token": user.partner_id._get_im_status_access_token(),
                "is_company": False,
                "main_user_id": user.id,
                "mention_token": user.partner_id._get_mention_token(),
                "name": "test15",
                "write_date": fields.Datetime.to_string(user.partner_id.write_date),
            }
        if user == self.user_root:
            return {
                "avatar_128_access_token": user.partner_id._get_avatar_128_access_token(),
                "id": user.partner_id.id,
                "is_company": False,
                "main_user_id": user.id,
                "name": "OdooBot",
                "write_date": fields.Datetime.to_string(user.partner_id.write_date),
            }
        if guest:
            return {
                "avatar_128_access_token": self.guest._get_avatar_128_access_token(),
                "country_id": self.guest.country_id.id,
                "id": self.guest.id,
                "im_status": "offline",
                "im_status_access_token": self.guest._get_im_status_access_token(),
                "name": "Visitor",
                "offline_since": False,
                "write_date": fields.Datetime.to_string(self.guest.write_date),
            }
        return {}