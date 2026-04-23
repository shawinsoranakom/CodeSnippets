def _prepare_message_data(self, post_data, *, thread, **kwargs):
        res = {
            key: value
            for key, value in post_data.items()
            if key in thread._get_allowed_message_params()
        }
        if (attachment_ids := post_data.get("attachment_ids")) is not None:
            attachments = request.env["ir.attachment"].browse(map(int, attachment_ids))
            if not attachments._has_attachments_ownership(post_data.get("attachment_tokens")):
                msg = self.env._(
                    "One or more attachments do not exist, or you do not have the rights to access them.",
                )
                raise UserError(msg)
            res["attachment_ids"] = attachments.ids
        if "body" in post_data:
            # User input is HTML string, so it needs to be in a Markup.
            # It will be sanitized by the field itself when writing on it.
            res["body"] = Markup(post_data["body"]) if post_data["body"] else post_data["body"]
        partner_ids = post_data.get("partner_ids")
        partner_emails = post_data.get("partner_emails")
        role_ids = post_data.get("role_ids")
        if partner_ids is not None or partner_emails is not None or role_ids is not None:
            partners = request.env["res.partner"].browse(map(int, partner_ids or []))
            if partner_emails:
                partners |= thread._partner_find_from_emails_single(
                    partner_emails,
                    no_create=not request.env.user.has_group("base.group_partner_manager"),
                )
            if role_ids:
                # sudo - res.users: getting partners linked to the role is allowed.
                partners |= (
                    request.env["res.users"]
                    .sudo()
                    .search_fetch([("role_ids", "in", role_ids)], ["partner_id"])
                    .partner_id
                )
            res["partner_ids"] = partners.filtered(
                lambda p: (not self.env.user.share and p.has_access("read"))
                or (
                    verify_limited_field_access_token(
                        p,
                        "id",
                        post_data.get("partner_ids_mention_token", {}).get(str(p.id), ""),
                        scope="mail.message_mention",
                    )
                ),
            ).ids
        res.setdefault("message_type", "comment")
        return res