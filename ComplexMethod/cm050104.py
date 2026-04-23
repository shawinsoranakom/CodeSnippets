def iap_enrich(self, *, batch_size=50):
        from_cron = bool(self.env.context.get('cron_id'))
        send_notification = not from_cron

        def process_leads(leads):
            lead_emails = {}
            for lead in leads:
                # If lead is lost, active == False, but is anyway removed from the search in the cron.
                if lead.probability == 100 or lead.iap_enrich_done:
                    continue
                # Skip if no email (different from wrong email leading to no email_normalized)
                if not lead.email_from:
                    continue

                normalized_email = tools.email_normalize(lead.email_from)
                if not normalized_email:
                    lead.write({'iap_enrich_done': True})
                    lead.message_post_with_source(
                        'crm_iap_enrich.mail_message_lead_enrich_no_email',
                        subtype_xmlid='mail.mt_note',
                    )
                    continue

                email_domain = normalized_email.split('@')[1]
                # Discard domains of generic email providers as it won't return relevant information
                if email_domain in iap_tools._MAIL_PROVIDERS:
                    lead.write({'iap_enrich_done': True})
                    lead.message_post_with_source(
                        'crm_iap_enrich.mail_message_lead_enrich_notfound',
                        subtype_xmlid='mail.mt_note',
                    )
                else:
                    lead_emails[lead.id] = email_domain
            if not lead_emails:
                return

            try:
                iap_response = self.env['iap.enrich.api']._request_enrich(lead_emails)
            except iap_tools.InsufficientCreditError:
                _logger.info('Lead enrichment failed because of insufficient credit')
                if send_notification:
                    self.env['iap.account']._send_no_credit_notification(
                        service_name='reveal',
                        title=_("Not enough credits for Lead Enrichment"))
                raise
            except Exception as e:
                if send_notification:
                    self.env['iap.account']._send_error_notification(
                        message=_('An error occurred during lead enrichment'))
                _logger.info('An error occurred during lead enrichment: %s', e)
                return
            else:
                if send_notification:
                    self.env['iap.account']._send_success_notification(
                        message=_("The leads/opportunities have successfully been enriched"))
                _logger.info('Batch of %s leads successfully enriched', len(lead_emails))
            self._iap_enrich_from_response(iap_response)

        if from_cron:
            self.env['ir.cron']._commit_progress(remaining=len(self))
        all_lead_ids = OrderedSet(self.ids)
        while all_lead_ids:
            leads = self.browse(all_lead_ids).try_lock_for_update(limit=batch_size)
            if not leads:
                _logger.error('A batch of leads could not be enriched (locked): %s', repr(self.browse(all_lead_ids)))
                # all are locked, schedule the cron later when the records might be unlocked
                self.env.ref('crm_iap_enrich.ir_cron_lead_enrichment')._trigger(self.env.cr.now() + datetime.timedelta(minutes=5))
                if from_cron:
                    # mark the cron as fully done to prevent immediate reschedule
                    self.env['ir.cron']._commit_progress(remaining=0)
                break
            all_lead_ids -= set(leads._ids)

            if from_cron:
                # Using commit progress for processed leads
                try:
                    process_leads(leads)
                    time_left = self.env['ir.cron']._commit_progress(len(leads))
                except iap_tools.InsufficientCreditError:
                    # Since there are no credits left, there is no point to process the other batches
                    # set remaining=0 to avoid being called again
                    self.env['ir.cron']._commit_progress(remaining=0)
                    break
                except Exception:
                    self.env.cr.rollback()
                    _logger.error('A batch of leads could not be enriched: %s', repr(leads))
                    time_left = self.env['ir.cron']._commit_progress(len(leads))
                if not time_left:
                    break
            else:
                # Commit processed batch to avoid complete rollbacks and therefore losing credits.
                try:
                    if modules.module.current_test:
                        with self.env.cr.savepoint():
                            process_leads(leads)
                    else:
                        process_leads(leads)
                        self.env.cr.commit()
                except iap_tools.InsufficientCreditError:
                    # Since there are no credits left, there is no point to process the other batches
                    break
                except Exception:
                    if not modules.module.current_test:
                        self.env.cr.rollback()
                    _logger.error('A batch of leads could not be enriched: %s', repr(leads))