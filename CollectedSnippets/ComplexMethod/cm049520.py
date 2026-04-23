def _nemhandel_deregister_participant(self):
        self.ensure_one()

        if self.company_id.l10n_dk_nemhandel_proxy_state == 'receiver':
            # fetch all documents and message statuses before unlinking the edi user
            # so that the invoices are acknowledged
            self._cron_nemhandel_get_message_status()
            self._cron_nemhandel_get_new_documents()
            if not tools.config['test_enable'] and not modules.module.current_test:
                self.env.cr.commit()

        if self.company_id.l10n_dk_nemhandel_proxy_state != 'not_registered':
            try:
                self._call_nemhandel_proxy(endpoint='/api/nemhandel/1/cancel_nemhandel_registration')
            except UserError as e:
                if e.args and e.args[0] != "The user doesn't exist on the proxy":
                    raise

        self.company_id.l10n_dk_nemhandel_proxy_state = 'not_registered'
        self.unlink()