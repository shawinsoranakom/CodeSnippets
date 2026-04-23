def _routing_check_route(self, message, message_dict, route, raise_exception=True):
        """ Verify route validity. Check and rules:
            1 - if thread_id -> check that document effectively exists; otherwise
                fallback on a message_new by resetting thread_id
            2 - check that message_update exists if thread_id is set; or at least
                that message_new exist
            3 - if there is an alias, check alias_contact:
                'followers' and thread_id:
                    check on target document that the author is in the followers
                'followers' and alias_parent_thread_id:
                    check on alias parent document that the author is in the
                    followers
                'partners': check that author_id id set

        Note that this method also updates 'author_id' of message_dict as route
        links an incoming message to a record and linking email to partner is
        better done in a record's context.

        :param message: an email.message instance
        :param message_dict: dictionary of values that will be given to
                             mail_message.create()
        :param route: route to check which is a tuple (model, thread_id,
                      custom_values, uid, alias)
        :param raise_exception: if an error occurs, tell whether to raise an error
                                or just log a warning and try other processing or
                                invalidate route
        """

        assert isinstance(route, (list, tuple)), 'A route should be a list or a tuple'
        assert len(route) == 5, 'A route should contain 5 elements: model, thread_id, custom_values, uid, alias record'

        message_id = message_dict['message_id']
        email_from = message_dict['email_from']
        model, thread_id, alias = route[0], route[1], route[4]
        record_set = None

        # Wrong model
        if not model:
            self._routing_warn(_('target model unspecified'), message_id, route, raise_exception)
            return ()
        if model not in self.env:
            self._routing_warn(_('unknown target model %s', model), message_id, route, raise_exception)
            return ()
        record_set = self.env[model].browse(thread_id) if thread_id else self.env[model]

        # Existing Document: check if exists and model accepts the mailgateway; if not, fallback on create if allowed
        if thread_id:
            if not record_set.exists():
                self._routing_warn(
                    _('reply to missing document (%(model)s,%(thread)s), fall back on document creation', model=model, thread=thread_id),
                    message_id,
                    route,
                    False
                )
                thread_id = None
            elif not hasattr(record_set, 'message_update'):
                self._routing_warn(_('reply to model %s that does not accept document update, fall back on document creation', model), message_id, route, False)
                thread_id = None

        # New Document: check model accepts the mailgateway
        if not thread_id and model and not hasattr(record_set, 'message_new'):
            self._routing_warn(_('model %s does not accept document creation', model), message_id, route, raise_exception)
            return ()

        # Alias: check alias_contact settings
        if alias:
            # Update message author. We do it now because we need it for aliases contact
            # settings check. Not great to do it in middle of route processing but hey
            if not message_dict.get('author_id'):
                link_doc = record_set
                if not link_doc and alias and alias.alias_parent_model_id and alias.alias_parent_thread_id:
                    link_doc = self.env[alias.alias_parent_model_id.model].browse(alias.alias_parent_thread_id)
                link_doc = link_doc if link_doc and hasattr(link_doc, '_partner_find_from_emails_single') else self.env['mail.thread']
                authors = link_doc._partner_find_from_emails_single([email_from], no_create=True)
                if authors:
                    message_dict['author_id'] = authors[0].id

            if thread_id:
                obj = record_set[0]
            elif alias.alias_parent_model_id and alias.alias_parent_thread_id:
                obj = self.env[alias.alias_parent_model_id.model].browse(alias.alias_parent_thread_id)
            else:
                obj = self.env[model]
            error = obj._alias_get_error(message, message_dict, alias)
            if error:
                self._routing_warn(
                    _('alias %(name)s: %(error)s', name=alias.alias_name, error=error.message or _('unknown error')),
                    message_id,
                    route,
                    False
                )
                alias._alias_bounce_incoming_email(message, message_dict, set_invalid=error.is_config_error)
                return False

        return (model, thread_id, route[2], route[3], route[4])