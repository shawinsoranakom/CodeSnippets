def _notify_thread_by_inbox(self, message, recipients_data, msg_vals=False, **kwargs):
        """ Notify recipients inbox of a message. It is done in two main steps

          * create inbox notifications for users;
          * send bus notifications;

        :param record message: <mail.message> record being notified. May be
          void as 'msg_vals' superseeds it;
        :param list recipients_data: list of recipients data based on <res.partner>
          records formatted like a list of dicts containing information. See
          ``MailThread._notify_get_recipients()``;
        :param dict msg_vals: values dict used to create the message, allows to
          skip message usage and spare some queries if given;
        """
        inbox_pids_uids = sorted(
            [(r["id"], r["uid"]) for r in recipients_data if r["id"] and r["notif"] == "inbox"]
        )
        if inbox_pids_uids:
            notif_create_values = [
                {
                    "author_id": message.author_id.id,
                    "mail_message_id": message.id,
                    "notification_status": "sent",
                    "notification_type": "inbox",
                    "res_partner_id": pid_uid[0],
                }
                for pid_uid in inbox_pids_uids
            ]
            # sudo: mail.notification - creating notifications is the purpose of notify methods
            self.env["mail.notification"].sudo().create(notif_create_values)
            users = self.env["res.users"].browse(i[1] for i in inbox_pids_uids if i[1])
            # sudo: mail.followers - reading followers of target users in batch to send it to them
            followers = self.env["mail.followers"].sudo().search(
                [
                    ("res_model", "=", message.model),
                    ("res_id", "=", message.res_id),
                    ("partner_id", "in", users.partner_id.ids),
                ]
            )
            for user in users:
                store = Store(bus_channel=user).add(
                    message.with_user(user).with_context(allowed_company_ids=[]),
                    msg_vals=msg_vals,
                    add_followers=True,
                    followers=followers,
                )
                user._bus_send(
                    "mail.message/inbox",
                    {
                        "message_id": message.id,
                        "store_data": store.get_result(),
                    }
                )