def _get_forbidden_access(self, operation: str) -> api.Self:
        """ Return the subset of ``self`` that does not satisfy the specific
        conditions for messages.
        """
        forbidden = self.browse()

        # Non employees see only messages with a subtype (aka, not internal logs)
        if not self.env.user._is_internal():
            message_type_condition = ''
            if operation in ('create', 'read'):
                message_type_condition = "message.message_type = 'comment' AND"
            rows = self.env.execute_query(SQL(
                ''' SELECT message.id
                    FROM "mail_message" AS message
                    LEFT JOIN "mail_message_subtype" as subtype ON message.subtype_id = subtype.id
                    WHERE %s message.id = ANY (%%s)
                        AND (message.is_internal IS TRUE OR message.subtype_id IS NULL OR subtype.internal IS TRUE)
                ''' % message_type_condition,
                self.ids,
            ))
            if rows:
                internal = self.browse(id_ for [id_] in rows)
                forbidden += internal
                self -= internal  # noqa: PLW0642
            if not self:
                return forbidden

        # Read the value of messages in order to determine their accessibility.
        # The values are put in 'messages_to_check', and entries are popped
        # once we know they are accessible. At the end, the remaining entries
        # are the invalid ones.
        self.flush_recordset(['model', 'res_id', 'author_id', 'create_uid', 'parent_id', 'message_type', 'partner_ids'])
        self.env['mail.notification'].flush_model(['mail_message_id', 'res_partner_id'])

        if operation in ('read', 'write'):
            query = SQL(
                """ SELECT m.id, m.model, m.res_id, m.author_id, m.create_uid, m.parent_id,
                        bool_or(partner_rel.res_partner_id IS NOT NULL OR needaction_rel.res_partner_id IS NOT NULL) AS notified,
                        m.message_type
                    FROM "mail_message" m
                    LEFT JOIN "mail_message_res_partner_rel" partner_rel
                        ON partner_rel.mail_message_id = m.id AND partner_rel.res_partner_id = %(pid)s
                    LEFT JOIN "mail_notification" needaction_rel
                        ON needaction_rel.mail_message_id = m.id AND needaction_rel.res_partner_id = %(pid)s
                    WHERE m.id = ANY(%(ids)s)
                    GROUP BY m.id
                """,
                pid=self.env.user.partner_id.id, ids=self.ids,
            )
        elif operation in ('create', 'unlink'):
            query = SQL(
                """ SELECT id, model, res_id, author_id, parent_id, message_type
                    FROM "mail_message"
                    WHERE id = ANY(%s)
                """, self.ids,
            )
        else:
            raise ValueError(_('Wrong operation name (%s)', operation))

        # trick: messages_to_check doesn't contain missing records from messages
        messages_to_check = {
            values['id']: values
            for values in self.env.execute_query_dict(query)
        }

        # Author condition (READ, WRITE, CREATE (private))
        partner_id = self.env.user.partner_id.id
        if operation == 'read':
            for mid, message in list(messages_to_check.items()):
                if (message.get('author_id') == partner_id
                        or message.get('create_uid') == self.env.uid):
                    messages_to_check.pop(mid)
        elif operation == 'write':
            for mid, message in list(messages_to_check.items()):
                if message.get('author_id') == partner_id:
                    messages_to_check.pop(mid)
        elif operation == 'create':
            for mid, message in list(messages_to_check.items()):
                if not self._is_thread_message_visible(vals=message):
                    messages_to_check.pop(mid)

        if not messages_to_check:
            return forbidden

        # Recipients condition, for read and write (partner_ids)
        # keep on top, usefull for systray notifications
        if operation in ('read', 'write'):
            for mid, message in list(messages_to_check.items()):
                if message.get('notified'):
                    messages_to_check.pop(mid)
            if not messages_to_check:
                return forbidden

        # CRUD: Access rights related to the document
        # {document_model_name: {document_id: message_ids}}
        model_docid_msgids = defaultdict(lambda: defaultdict(list))
        for mid, message in messages_to_check.items():
            if (message.get('model') and message.get('res_id') and
                    message.get('message_type') != 'user_notification'):
                model_docid_msgids[message['model']][message['res_id']].append(mid)
        for model, docid_msgids in model_docid_msgids.items():
            allowed = self._filter_records_for_message_operation(model, docid_msgids, operation)
            for doc_id, msg_ids in docid_msgids.items():
                if doc_id in allowed.ids:
                    for mid in msg_ids:
                        messages_to_check.pop(mid)

        if not messages_to_check:
            return forbidden

        # Parent condition, for create (check for received notifications for the created message parent)
        if operation == 'create':
            parent_ids_msg_ids = defaultdict(list)
            for mid, message in messages_to_check.items():
                if message.get('parent_id'):
                    parent_ids_msg_ids[message['parent_id']].append(mid)
            if parent_ids_msg_ids:
                query = SQL(
                    """ SELECT m.id
                        FROM "mail_message" m
                        JOIN "mail_message_res_partner_rel" partner_rel
                            ON partner_rel.mail_message_id = m.id AND partner_rel.res_partner_id = %s
                        WHERE m.id = ANY(%s) """,
                    self.env.user.partner_id.id, list(parent_ids_msg_ids),
                )
                for [parent_id] in self.env.execute_query(query):
                    for mid in parent_ids_msg_ids[parent_id]:
                        messages_to_check.pop(mid)

            if not messages_to_check:
                return forbidden

            # Recipients condition for create (message_follower_ids)
            for model, docid_msgids in model_docid_msgids.items():
                domain = [
                    ('res_model', '=', model),
                    ('res_id', 'in', list(docid_msgids)),
                    ('partner_id', '=', self.env.user.partner_id.id),
                ]
                followers = self.env['mail.followers'].sudo().search_fetch(domain, ['res_id'])
                for follower in followers:
                    for mid in docid_msgids[follower.res_id]:
                        messages_to_check.pop(mid)

            if not messages_to_check:
                return forbidden

        forbidden += self.browse(messages_to_check)
        return forbidden