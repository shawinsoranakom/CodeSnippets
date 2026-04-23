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