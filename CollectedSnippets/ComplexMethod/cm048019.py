def _call_peppol_proxy(self, endpoint, params=None):
        self.ensure_one()
        if self.proxy_type != 'peppol':
            raise UserError(_('EDI user should be of type Peppol'))

        token_out_of_sync_error_message = self.env._(
            "Failed to connect to Peppol Access Point. This might happen if you restored a database from a backup or copied it without neutralization. "
            "To fix this, please go to Settings > Accounting > Peppol Settings and click on 'Reconnect this database'."
        )

        if self.is_token_out_of_sync:
            raise UserError(token_out_of_sync_error_message)

        params = params or {}
        try:
            response = self._make_request(
                f"{self._get_server_url()}{endpoint}",
                params=params,
            )
        except AccountEdiProxyError as e:
            if (
                e.code == 'no_such_user'
                and not self.active
                and not self.company_id.account_edi_proxy_client_ids.filtered(lambda u: u.proxy_type == 'peppol')
            ):
                self.company_id.write({
                    'account_peppol_proxy_state': 'not_registered',
                    'account_peppol_migration_key': False,
                })
                # commit the above changes before raising below
                if not modules.module.current_test:
                    self.env.cr.commit()
                raise UserError(_('We could not find a user with this information on our server. Please check your information.'))

            elif e.code == 'invalid_signature':
                self._mark_connection_out_of_sync()
                if not tools.config['test_enable'] and not modules.module.current_test:
                    self.env.cr.commit()
                raise UserError(token_out_of_sync_error_message)
            raise UserError(e.message)

        if error_vals := response.get('error'):
            error_message = get_peppol_error_message(self.env, error_vals)
            raise UserError(error_message)

        return response