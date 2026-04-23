def _fetch_mail(self, batch_limit=50) -> Exception | None:
        """ Fetch e-mails from multiple servers.

        Commit after each message.
        """
        result_exception = None
        servers = self.with_context(fetchmail_cron_running=True)
        total_remaining = len(servers)  # number of unseen messages + number of unchecked servers
        self.env['ir.cron']._commit_progress(remaining=total_remaining)
        _logger.info("Fetchmail servers (in order) to be processed %s", servers.mapped('name'))

        for server in servers:
            total_remaining -= 1  # the server is checked
            if not server.try_lock_for_update(allow_referencing=True).filtered_domain(MAIL_SERVER_DOMAIN):
                _logger.info('Skip checking for new mails on mail server id %d (unavailable)', server.id)
                continue
            server_type_and_name = server.server_type, server.name  # avoid reading this after each commit
            _logger.info('Start checking for new emails on %s server %s', *server_type_and_name)
            count, failed = 0, 0

            # processing messages in a separate transaction to keep lock on the server
            server_connection = None
            message_cr = None
            try:
                server_connection = server._connect__()
                message_cr = self.env.registry.cursor()
                MailThread = server.env['mail.thread'].with_env(self.env(cr=message_cr)).with_context(default_fetchmail_server_id=server.id)
                thread_process_message = functools.partial(
                    MailThread.message_process,
                    model=server.object_id.model,
                    save_original=server.original,
                    strip_attachments=(not server.attach),
                )
                unread_message_count = server_connection.check_unread_messages()
                _logger.debug('%d unread messages on %s server %s.', unread_message_count, *server_type_and_name)
                total_remaining += unread_message_count
                for message_num, message in server_connection.retrieve_unread_messages():
                    _logger.debug('Fetched message %r on %s server %s.', message_num, *server_type_and_name)
                    count += 1
                    total_remaining -= 1
                    try:
                        thread_process_message(message=message)
                        remaining_time = MailThread.env['ir.cron']._commit_progress(1)
                    except Exception:  # noqa: BLE001
                        MailThread.env.cr.rollback()
                        failed += 1
                        _logger.info('Failed to process mail from %s server %s.', *server_type_and_name, exc_info=True)
                        # mail failed, but still "seen", so one unit of work
                        remaining_time = MailThread.env['ir.cron']._commit_progress(1)
                    server_connection.handled_message(message_num)
                    if count >= batch_limit or not remaining_time:
                        break
                server.error_date = False
                server.error_message = False
            except Exception as e:  # noqa: BLE001
                result_exception = e
                _logger.info("General failure when trying to fetch mail from %s server %s.", *server_type_and_name, exc_info=True)
                if not server.error_date:
                    server.error_date = fields.Datetime.now()
                    server.error_message = exception_to_unicode(e)
                elif server.error_date < fields.Datetime.now() - MAIL_SERVER_DEACTIVATE_TIME:
                    message = "Deactivating fetchmail %s server %s (too many failures)" % server_type_and_name
                    server.set_draft()
                    server.env['ir.cron']._notify_admin(message)
            finally:
                if message_cr is not None:
                    message_cr.close()
                try:
                    if server_connection:
                        server_connection.disconnect()
                except (OSError, IMAP4.abort):
                    _logger.warning('Failed to properly finish %s connection: %s.', *server_type_and_name, exc_info=True)
            _logger.info("Fetched %d email(s) on %s server %s; %d succeeded, %d failed.", count, *server_type_and_name, (count - failed), failed)
            server.write({'date': fields.Datetime.now()})
            # Commit before updating the progress because progress may be
            # updated for messages using another transaction. Without a commit
            # before updating the progress, we would have a serialization error.
            self.env.cr.commit()
            # checked server, so one unit of work done (even if no messages fetched on server)
            remaining_time = self.env['ir.cron']._commit_progress(1, remaining=total_remaining)
            if not remaining_time:
                break
        return result_exception