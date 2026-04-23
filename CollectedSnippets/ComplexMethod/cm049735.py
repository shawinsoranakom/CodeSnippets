def _prepare_message_values(self, documents, model_name):
        return {
            "body": (len(documents) > 1 and (", ".join(documents.mapped('display_name')) + "\n") or "") + (self.message or ""),
            "email_add_signature": False,
            "email_from": self.env.user.email_formatted,
            "email_layout_xmlid": len(documents) > 1 and "mail.mail_notification_multi_invite" or "mail.mail_notification_invite",
            "model": self.res_model,
            "reply_to": self.env.user.email_formatted,
            "reply_to_force_new": True,
            "subject": len(documents) > 1 and self.env._(
                "Invitation to follow %(document_model)s.",
                document_model=model_name,
            ) or self.env._(
                "Invitation to follow %(document_model)s: %(document_name)s",
                document_model=model_name,
                document_name=documents.display_name,
            )
        }