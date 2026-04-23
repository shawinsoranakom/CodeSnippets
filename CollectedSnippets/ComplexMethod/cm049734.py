def edit_followers(self):
        for wizard in self:
            res_ids = parse_res_ids(wizard.res_ids, self.env)
            documents = self.env[wizard.res_model].browse(res_ids)
            if not documents:
                raise UserError(self.env._("No documents found for the selected records."))
            if wizard.operation == "remove":
                documents.message_unsubscribe(partner_ids=wizard.partner_ids.ids)
            else:
                if not self.env.user.email:
                    raise UserError(
                        self.env._(
                            "Unable to post message, please configure the sender's email address."
                        )
                    )
                documents.message_subscribe(partner_ids=wizard.partner_ids.ids)
                if wizard.notify:
                    model_name = self.env["ir.model"]._get(wizard.res_model).display_name
                    message_values = wizard._prepare_message_values(documents, model_name)
                    message_values["partner_ids"] = wizard.partner_ids.ids
                    documents[0].message_notify(**message_values)
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
            "type": "success",
            "message": self.env._("Followers updated") if len(wizard) > 1 else (
                self.env._("Followers added") if wizard.operation == "add" else self.env._("Followers removed")
            ),
            "sticky": False,
            "next": {"type": "ir.actions.act_window_close"},
            },
        }