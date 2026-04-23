def _to_store(self, store: Store, fields, *, format_reply=True, msg_vals=False, add_followers=False, followers=None):
        """Add the messages to the given store.

        :param format_reply: if True, also get data about the parent message if it exists.
            Only makes sense for discuss channel.

        :param msg_vals: dictionary of values used to create the message. If
          given it may be used to access values related to ``message`` without
          accessing it directly. It lessens query count in some optimized use
          cases by avoiding access message content in db;

        :param add_followers: if True, also add followers of the current target for each thread of
            each message. Only applicable if ``store.target`` is a specific user.

        :param followers: if given, use this pre-computed list of followers instead of fetching
            them. It lessen query count in some optimized use cases.
            Only applicable if ``add_followers`` is True.
        """
        if "message_format" not in fields:
            store.add_records_fields(self, fields)
            return
        fields.remove("message_format")
        # fetch scheduled notifications once, only if msg_vals is not given to
        # avoid useless queries when notifying Inbox right after a message_post
        scheduled_dt_by_msg_id = {}
        if msg_vals:
            scheduled_dt_by_msg_id = {msg.id: msg_vals.get("scheduled_date", False) for msg in self}
        elif self:
            schedulers = self.env["mail.message.schedule"].sudo().search([("mail_message_id", "in", self.ids)])
            for scheduler in schedulers:
                scheduled_dt_by_msg_id[scheduler.mail_message_id.id] = scheduler.scheduled_datetime
        record_by_message = self._record_by_message()
        records = record_by_message.values()
        non_channel_records = filter(lambda record: record._name != "discuss.channel", records)
        target_user = store.target.get_user(self.env)
        if target_user and add_followers and non_channel_records:
            if followers is None:
                domain = Domain.OR(
                    [("res_model", "=", model), ("res_id", "in", [r.id for r in records])]
                    for model, records in groupby(non_channel_records, key=lambda r: r._name)
                )
                domain &= Domain("partner_id", "=", target_user.partner_id.id)
                # sudo: mail.followers - reading followers of current partner
                followers = self.env["mail.followers"].sudo().search(domain)
            follower_by_record_and_partner = {
                (
                    self.env[follower.res_model].browse(follower.res_id),
                    follower.partner_id,
                ): follower
                for follower in followers
            }
        record_fields = [
            # sudo: mail.thread - if mentionned in a non accessible thread, name is allowed
            Store.Attr("display_name", sudo=True),
            Store.Attr("has_mail_thread", lambda record: isinstance(record, self.env.registry["mail.thread"])),
            Store.Attr(
                "module_icon",
                lambda record: modules.module.get_module_icon(self.env[record._name]._original_module),
                predicate=lambda record: self.env[record._name]._original_module,
            ),
        ]
        if target_user and add_followers and non_channel_records:
            record_fields.append(
                Store.One(
                    "selfFollower",
                    ["is_active", Store.One("partner_id", [])],
                    value=lambda r: follower_by_record_and_partner.get((r, target_user.partner_id)),
                ),
            )
        for record in records:
            store.add(record, record_fields, as_thread=True)
        if store.target.is_current_user(self.env):
            fields.append("starred")
        store.add(self, fields)
        for message in self:
            record = record_by_message.get(message)
            if record:
                try:
                    if hasattr(record, "_message_compute_subject"):
                        # sudo: if mentionned in a non accessible thread, user should be able to see the subject
                        default_subject = record.sudo()._message_compute_subject()
                    else:
                        default_subject = message.record_name
                except MissingError:
                    record = None
                    default_subject = False
            else:
                default_subject = False
            data = {
                "default_subject": default_subject,
                "scheduledDatetime": scheduled_dt_by_msg_id.get(message.id, False),
                "thread": Store.One(record, [], as_thread=True),
            }

            if message.incoming_email_cc:
                data["incoming_email_cc"] = tools.mail.email_split_tuples(message.incoming_email_cc)
            if message.incoming_email_to:
                data["incoming_email_to"] = tools.mail.email_split_tuples(message.incoming_email_to)
            if store.target.is_current_user(self.env):
                # sudo: mail.message - filtering allowed tracking values
                displayed_tracking_ids = message.sudo().tracking_value_ids._filter_has_field_access(
                    self.env
                )
                if record and hasattr(record, "_track_filter_for_display"):
                    displayed_tracking_ids = record._track_filter_for_display(
                        displayed_tracking_ids
                    )
                # sudo: mail.message - checking whether there is a notification for the current user is acceptable
                notifications_partners = message.sudo().notification_ids.filtered(
                    lambda n: not n.is_read
                ).res_partner_id
                data["needaction"] = (
                    not self.env.user._is_public()
                    and self.env.user.partner_id in notifications_partners
                )
                data["trackingValues"] = displayed_tracking_ids._tracking_value_format()
            store.add(message, data)
        # Add extras at the end to guarantee order in result. In particular, the parent message
        # needs to be after the current message (client code assuming the first received message is
        # the one just posted for example, and not the message being replied to).
        self._extras_to_store(store, format_reply=format_reply)