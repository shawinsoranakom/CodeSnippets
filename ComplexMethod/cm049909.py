def _thread_to_store(self, store: Store, fields, *, request_list=None):
        is_request = request_list is not None
        request_list = request_list or []
        store.add_records_fields(self, fields, as_thread=True)
        for thread in self:
            res = {}
            if is_request and store.target.is_current_user(self.env):
                res["hasReadAccess"] = thread.sudo(False).has_access("read")
                res["hasWriteAccess"] = thread.sudo(False).has_access("write")
                res["canPostOnReadonly"] = self._mail_get_operation_for_mail_message_operation('create').get(self) == "read"
            if (
               "activities" in request_list
                and isinstance(self.env[self._name], self.env.registry["mail.activity.mixin"])
            ):
                res["activities"] = Store.Many(thread.with_context(active_test=True).activity_ids)
            if "attachments" in request_list:
                res["attachments"] = Store.Many(thread._get_mail_thread_data_attachments())
                res["areAttachmentsLoaded"] = True
                res["isLoadingAttachments"] = False
            if "contact_fields" in request_list:
                res["primary_email_field"] = thread._mail_get_primary_email_field()
                res["partner_fields"] = thread._mail_get_partner_fields()
            if "followers" in request_list:
                res["followersCount"] = self.env["mail.followers"].search_count(
                    [("res_id", "=", thread.id), ("res_model", "=", self._name)]
                )
                self_follower = self.env["mail.followers"].search(
                    [
                        ("res_id", "=", thread.id),
                        ("res_model", "=", self._name),
                        ["partner_id", "=", self.env.user.partner_id.id],
                    ]
                )
                res["selfFollower"] = Store.One(self_follower)
                thread._message_followers_to_store(store, reset=True)
                subtype_id = self.env["ir.model.data"]._xmlid_to_res_id("mail.mt_comment")
                res["recipientsCount"] = self.env["mail.followers"].search_count(
                    [
                        ("res_id", "=", thread.id),
                        ("res_model", "=", self._name),
                        ("partner_id", "!=", self.env.user.partner_id.id),
                        ("subtype_ids", "=", subtype_id),
                        ("partner_id.active", "=", True),
                    ]
                )
                thread._message_followers_to_store(store, filter_recipients=True, reset=True)
            if "display_name" in request_list:
                res["display_name"] = thread.display_name
            if "scheduledMessages" in request_list:
                res["scheduledMessages"] = Store.Many(self.env['mail.scheduled.message'].search([
                    ['model', '=', self._name], ['res_id', '=', thread.id]
                ]))
            if "suggestedRecipients" in request_list:
                res["suggestedRecipients"] = thread._message_get_suggested_recipients(
                    reply_discussion=True, no_create=True,
                )
            if res:
                store.add(thread, res, as_thread=True)