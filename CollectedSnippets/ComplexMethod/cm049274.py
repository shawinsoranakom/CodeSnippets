def test_06_web_image_attachment_access(self):
        """Tests all the combination of user/ways to access an attachment through `/web/content`
        or `/web/image` routes"""
        new_test_user(self.env, "portal_user", groups="base.group_portal")
        new_test_user(self.env, "internal_user")
        # record of arbitrary model with restrictive ACL even for internal users
        restricted_record = self.env["res.users.settings"].create({"user_id": self.env.user.id})
        # record of arbitrary model with permissive ACL for internal users
        accessible_record = self.env["res.partner"].create({"name": "test partner"})
        attachments = self.env["ir.attachment"].create(
            [
                {
                    "datas": b"R0lGODdhAQABAIAAAP///////ywAAAAAAQABAAACAkQBADs=",
                    "description": "restricted attachment",
                    "name": "test.gif",
                    "res_id": restricted_record.id,
                    "res_model": restricted_record._name,
                },
                {
                    "datas": b"R0lGODdhAQABAIAAAP///////ywAAAAAAQABAAACAkQBADs=",
                    "description": "restricted attachment",
                    "name": "test.gif",
                    "res_id": accessible_record.id,
                    "res_model": accessible_record._name,
                },
                {
                    "datas": b"R0lGODdhAQABAIAAAP///////ywAAAAAAQABAAACAkQBADs=",
                    "description": "standalone attachment",
                    "name": "test.gif",
                },
                {
                    "datas": b"R0lGODdhAQABAIAAAP///////ywAAAAAAQABAAACAkQBADs=",
                    "description": "public attachment",
                    "name": "test.gif",
                    "public": True,
                },
            ]
        )
        attachments.generate_access_token()
        internal_restricted, internal_accessible, standalone, public = attachments
        tests = [
            # (attachment, user, token, expected result (True if accessible))
            (internal_restricted, "public_user", None, False),
            (internal_restricted, "public_user", "token", True),
            (internal_restricted, "public_user", "limited token", True),
            (internal_restricted, "portal_user", None, False),
            (internal_restricted, "portal_user", "token", True),
            (internal_restricted, "portal_user", "limited token", True),
            (internal_restricted, "internal_user", None, False),
            (internal_restricted, "internal_user", "token", True),
            (internal_restricted, "internal_user", "limited token", True),
            (internal_accessible, "public_user", None, False),
            (internal_accessible, "public_user", "token", True),
            (internal_accessible, "public_user", "limited token", True),
            (internal_accessible, "portal_user", None, False),
            (internal_accessible, "portal_user", "token", True),
            (internal_accessible, "portal_user", "limited token", True),
            (internal_accessible, "internal_user", None, True),
            (internal_accessible, "internal_user", "token", True),
            (internal_accessible, "internal_user", "limited token", True),
            (standalone, "public_user", None, False),
            (standalone, "public_user", "token", True),
            (standalone, "public_user", "limited token", True),
            (standalone, "portal_user", None, False),
            (standalone, "portal_user", "token", True),
            (standalone, "portal_user", "limited token", True),
            (standalone, "internal_user", None, False),
            (standalone, "internal_user", "token", True),
            (standalone, "internal_user", "limited token", True),
            (public, "public_user", None, True),
            (public, "public_user", "token", True),
            (public, "public_user", "limited token", True),
            (public, "portal_user", None, True),
            (public, "portal_user", "token", True),
            (public, "portal_user", "limited token", True),
            (public, "internal_user", None, True),
            (public, "internal_user", "token", True),
            (public, "internal_user", "limited token", True),
        ]
        for attachment, user, token, result in tests:
            login = None if user == "public_user" else user
            self.authenticate(login, login)
            access_token_param = ""
            if token:
                access_token = (
                    attachment.access_token
                    if token == "token"
                    else attachment._get_raw_access_token()
                )
                access_token_param = f"?access_token={access_token}"
            res = self.url_open(f"/web/image/{attachment.id}{access_token_param}")
            if result:
                self.assertEqual(
                    res.headers["Content-Disposition"],
                    "inline; filename=test.gif",
                    f"{user} should have access to {attachment.description} with {token or 'no token'}",
                )
            else:
                self.assertEqual(
                    res.headers["Content-Disposition"],
                    "inline; filename=placeholder.png",
                    f"{user} should not have access to {attachment.description} with {token or 'no token'}",
                )