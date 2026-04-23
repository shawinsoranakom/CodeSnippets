def message_process(self, model, message, custom_values=None,
                        save_original=False, strip_attachments=False,
                        thread_id=None):
        """ Process an incoming RFC2822 email message, relying on
            ``mail.message.parse()`` for the parsing operation,
            and ``message_route()`` to figure out the target model.

            Once the target model is known, its ``message_new`` method
            is called with the new message (if the thread record did not exist)
            or its ``message_update`` method (if it did).

           :param str model: the fallback model to use if the message
               does not match any of the currently configured mail aliases
               (may be None if a matching alias is supposed to be present)
           :param message: source of the RFC2822 message
           :type message: str | xmlrpclib.Binary
           :param custom_values: optional dictionary of field values
                to pass to ``message_new`` if a new record needs to be created.
                Ignored if the thread record already exists, and also if a
                matching mail.alias was found (aliases define their own defaults)
           :type custom_values: dict | None
           :param bool save_original: whether to keep a copy of the original
                email source attached to the message after it is imported.
           :param bool strip_attachments: whether to strip all attachments
                before processing the message, in order to save some space.
           :param int thread_id: optional ID of the record/thread from ``model``
               to which this mail should be attached. When provided, this
               overrides the automatic detection based on the message
               headers.
        """
        # extract message bytes - we are forced to pass the message as binary because
        # we don't know its encoding until we parse its headers and hence can't
        # convert it to utf-8 for transport between the mailgate script and here.
        if isinstance(message, xmlrpclib.Binary):
            message = bytes(message.data)
        if isinstance(message, str):
            message = message.encode('utf-8')
        message = email.message_from_bytes(message, policy=email.policy.SMTP)

        # parse the message, verify we are not in a loop by checking message_id is not duplicated
        msg_dict = self.message_parse(message, save_original=save_original)
        if strip_attachments:
            msg_dict.pop('attachments', None)

        msg_id = msg_dict.get('message_id')
        is_duplicate = bool(self.env['mail.message'].search_count([('message_id', '=', msg_id)], limit=1))
        if not is_duplicate and msg_id:
            # Synchronize concurrent transactions for the same message_id to make the duplicate check reliable.
            # Use pg_try_advisory_xact_lock: if another transaction is already processing the same message_id,
            # treat it as a duplicate.
            self.env.cr.execute(SQL('SELECT pg_try_advisory_xact_lock(hashtext(%s))', msg_id))
            is_duplicate = not self.env.cr.fetchone()[0]

        if is_duplicate:
            _logger.info('Ignored mail from %s to %s with Message-Id %s: found duplicated Message-Id during processing',
                         msg_dict.get('email_from'), msg_dict.get('to'), msg_id)
            return False

        if self._detect_loop_headers(msg_dict):
            _logger.info('Ignored mail from %s to %s with Message-Id %s: reply to a bounce notification detected by headers',
                             msg_dict.get('email_from'), msg_dict.get('to'), msg_dict.get('message_id'))
            return

        # find possible routes for the message; note this also updates notably
        # 'author_id' of msg_dict
        routes = self.message_route(message, msg_dict, model, thread_id, custom_values)
        if self._detect_loop_sender(message, msg_dict, routes):
            return

        # update document-dependant values
        msg_dict.update(**self._message_parse_post_process(message, msg_dict, routes))

        # process routes
        thread_id = self._message_route_process(message, msg_dict, routes)
        return thread_id