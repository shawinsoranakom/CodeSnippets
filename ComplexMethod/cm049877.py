def message_route(self, message, message_dict, model=None, thread_id=None, custom_values=None):
        """ Attempt to figure out the correct target model, thread_id,
        custom_values and user_id to use for an incoming message.
        Multiple values may be returned, if a message had multiple
        recipients matching existing mail.aliases, for example.

        The following heuristics are used, in this order:

         * if the message replies to an existing thread by having a Message-Id
           that matches an existing mail_message.message_id, we take the original
           message model/thread_id pair and ignore custom_value as no creation will
           take place;
         * look for a mail.alias entry matching the message recipients and use the
           corresponding model, thread_id, custom_values and user_id. This could
           lead to a thread update or creation depending on the alias;
         * fallback on provided ``model``, ``thread_id`` and ``custom_values``;
         * raise an exception as no route has been found

        :param str message: an email.message instance
        :param dict message_dict: dictionary holding parsed message variables
        :param str model: the fallback model to use if the message does not match
            any of the currently configured mail aliases (may be None if a matching
            alias is supposed to be present)
        :param custom_values: dictionary mapping field names
            to default values to be passed to ``message_new`` if a new record needs
            to be created. Ignored if the thread record already exists, and also
            if a matching mail.alias was found (aliases define their own defaults)
        :type custom_values: dict[str, Any] | None
        :param int thread_id: optional ID of the record/thread from ``model`` to
            which this mail should be attached. Only used if the message does not
            reply to an existing thread and does not match any mail alias.
        :return: list of routes [(model, thread_id, custom_values, user_id, alias)]

        :raises: ValueError, TypeError
        """
        if not isinstance(message, EmailMessage):
            raise TypeError('message must be an email.message.EmailMessage at this point')
        catchall_domains_allowed = list(filter(None, (self.env["ir.config_parameter"].sudo().get_param(
            "mail.catchall.domain.allowed") or '').split(',')))
        if catchall_domains_allowed:
            catchall_domains_allowed += self.env['mail.alias.domain'].search([]).mapped('name')

        def _filter_excluded_local_part(email):
            left, _at, domain = email.partition('@')
            if not domain:
                return False
            if catchall_domains_allowed and domain not in catchall_domains_allowed:
                return False
            return left

        fallback_model = model

        # handle bounce: verify whether this is a bounced email and use it to
        # collect bounce data and update notifications for customers
        if message_dict.get('is_bounce'):
            self._routing_handle_bounce(message, message_dict)
            return []
        self._routing_reset_bounce(message, message_dict)

        # get email.message.Message variables for future processing
        message_id = message_dict['message_id']

        # compute references to find if message is a reply to an existing thread
        thread_references = message_dict['references'] or message_dict['in_reply_to']
        msg_references = [r.strip() for r in unfold_references(thread_references) if 'reply_to' not in r]
        # avoid creating a gigantic query by limiting the number of references taken into account.
        # newer msg_ids are *appended* to References as per RFC5322 §3.6.4, so we should generally
        # find a match just with the last entry (equal to `In-Reply-To`). 32 refs seems large enough,
        # we've seen performance degrade with 100+ refs.
        msg_references = msg_references[-32:]
        replying_to_msg = self.env['mail.message'].sudo().search(
            [('message_id', 'in', msg_references)], limit=1, order='id desc'
        ) if msg_references else self.env['mail.message']
        is_a_reply, reply_model, reply_thread_id = bool(replying_to_msg), replying_to_msg.model, replying_to_msg.res_id

        # author and recipients
        email_from = message_dict['email_from']
        email_to_list = [e.lower() for e in email_split(message_dict['to'])]
        email_to_localparts = list(filter(None, (_filter_excluded_local_part(email_to) for email_to in email_to_list)))
        # Delivered-To is a safe bet in most modern MTAs, but we have to fallback on To + Cc values
        # for all the odd MTAs out there, as there is no standard header for the envelope's `rcpt_to` value.
        rcpt_tos_list = [e.lower() for e in email_split(message_dict['recipients'])]
        rcpt_tos_localparts = list(filter(None, (_filter_excluded_local_part(email_to) for email_to in rcpt_tos_list)))
        rcpt_tos_valid_list = list(rcpt_tos_list)

        # 1. Handle reply
        #    if destination = alias with different model -> consider it is a forward and not a reply
        #    if destination = alias with same model -> check contact settings as they still apply
        if reply_model and reply_thread_id:
            reply_model_id = self.env['ir.model']._get_id(reply_model)
            other_model_aliases = self.env['mail.alias'].search([
                '&',
                ('alias_model_id', '!=', reply_model_id),
                '|',
                ('alias_full_name', 'in', email_to_list),
                '&', ('alias_name', 'in', email_to_localparts), ('alias_incoming_local', '=', True),
            ])
            if other_model_aliases:
                is_a_reply, reply_model, reply_thread_id = False, False, False
                rcpt_tos_valid_list = [
                    to
                    for to in rcpt_tos_valid_list
                    if (
                        to in other_model_aliases.mapped('alias_full_name')
                        or to.split('@', 1)[0] in other_model_aliases.filtered('alias_incoming_local').mapped('alias_name')
                    )
                ]
        rcpt_tos_valid_localparts = list(filter(None, (_filter_excluded_local_part(email_to) for email_to in rcpt_tos_valid_list)))

        if is_a_reply and reply_model:
            reply_model_id = self.env['ir.model']._get_id(reply_model)
            dest_aliases = self.env['mail.alias'].search([
                '&',
                ('alias_model_id', '=', reply_model_id),
                '|',
                ('alias_full_name', 'in', rcpt_tos_list),
                '&', ('alias_name', 'in', rcpt_tos_localparts), ('alias_incoming_local', '=', True),
            ], limit=1)

            user_id = self._mail_find_user_for_gateway(email_from, alias=dest_aliases).id or self.env.uid
            route = self._routing_check_route(
                message, message_dict,
                (reply_model, reply_thread_id, custom_values, user_id, dest_aliases),
                raise_exception=False)
            if route:
                _logger.info(
                    'Routing mail from %s to %s with Message-Id %s: direct reply to msg: model: %s, thread_id: %s, custom_values: %s, uid: %s',
                    email_from, message_dict['to'], message_id, reply_model, reply_thread_id, custom_values, self.env.uid)
                return [route]
            if route is False:
                return []

        # 2. Handle new incoming email by checking aliases and applying their settings
        # prefetch catchall aliases as they are used several times
        catchall_aliases = self.env['mail.alias.domain'].search([]).mapped('catchall_email')
        self = self.with_context(mail_catchall_aliases=catchall_aliases)
        if rcpt_tos_list:
            # no route found for a matching reference (or reply), so parent is invalid
            message_dict.pop('parent_id', None)

            # check it does not directly contact catchall
            if self._detect_write_to_catchall(message_dict):
                _logger.info('Routing mail from %s to %s with Message-Id %s: direct write to catchall, bounce',
                             email_from, message_dict['to'], message_id)
                body = self.env['ir.qweb']._render('mail.mail_bounce_catchall', {
                    'message': message,
                })
                self._routing_create_bounce_email(
                    email_from, body, message,
                    # add a reference with a tag, to be able to ignore response to this email
                    references=f'{message_id} {generate_tracking_message_id("loop-detection-bounce-email")}',
                    reply_to=self.env.company.email)
                return []

            dest_aliases = self.env['mail.alias'].search([
                '|',
                ('alias_full_name', 'in', rcpt_tos_valid_list),
                '&', ('alias_name', 'in', rcpt_tos_valid_localparts), ('alias_incoming_local', '=', True),
            ])
            if dest_aliases:
                routes = []
                for alias in dest_aliases:
                    user_id = self._mail_find_user_for_gateway(email_from, alias=alias).id or self.env.uid
                    route = (alias.sudo().alias_model_id.model, alias.alias_force_thread_id, ast.literal_eval(alias.alias_defaults), user_id, alias)
                    AliasModel = self.env[route[0]] if route[0] in self.env and hasattr(self.env[route[0]], '_routing_check_route') else self
                    route = AliasModel._routing_check_route(message, message_dict, route, raise_exception=True)
                    if route:
                        _logger.info(
                            'Routing mail from %s to %s with Message-Id %s: direct alias match: %r',
                            email_from, message_dict['to'], message_id, route)
                        routes.append(route)
                return routes

        # 3. Fallback to the provided parameters, if they work
        if fallback_model:
            # no route found for a matching reference (or reply), so parent is invalid
            message_dict.pop('parent_id', None)
            user_id = self._mail_find_user_for_gateway(email_from).id or self.env.uid
            route = self._routing_check_route(
                message, message_dict,
                (fallback_model, thread_id, custom_values, user_id, None),
                raise_exception=True)
            if route:
                _logger.info(
                    'Routing mail from %s to %s with Message-Id %s: fallback to model:%s, thread_id:%s, custom_values:%s, uid:%s',
                    email_from, message_dict['to'], message_id, fallback_model, thread_id, custom_values, user_id)
                return [route]

        # 4. Recipients contain catchall and unroutable emails -> bounce
        if rcpt_tos_list and self.with_context(mail_catchall_write_any_to=True)._detect_write_to_catchall(message_dict):
            _logger.info(
                'Routing mail from %s to %s with Message-Id %s: write to catchall + other unroutable emails, bounce',
                email_from, message_dict['to'], message_id
            )
            body = self.env['ir.qweb']._render('mail.mail_bounce_catchall', {
                'message': message,
            })
            self._routing_create_bounce_email(
                email_from, body, message,
                # add a reference with a tag, to be able to ignore response to this email
                references=f'{message_id} {generate_tracking_message_id("loop-detection-bounce-email")}',
                reply_to=self.env.company.email)
            return []

        # ValueError if no routes found and if no bounce occurred
        raise ValueError(
            'No possible route found for incoming message from %s to %s (Message-Id %s:). '
            'Create an appropriate mail.alias or force the destination model.' %
            (email_from, message_dict['to'], message_id)
        )