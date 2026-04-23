def _peppol_get_participant_status(self):
        for edi_user in self:
            edi_user = edi_user.with_company(edi_user.company_id)
            if edi_user.proxy_type != 'peppol':
                continue
            try:
                proxy_user = edi_user._make_request(f"{edi_user._get_server_url()}/api/peppol/2/participant_status")
            except AccountEdiProxyError as e:
                if e.code == 'client_gone':
                    # reset the connection if it was archived/deleted on IAP side
                    edi_user.sudo().company_id._reset_peppol_configuration()
                    edi_user.action_archive()
                else:
                    # don't auto-deregister users on any other errors to avoid settings client-side to states
                    # that are not recoverable without user action if an error on IAP side ever occurs
                    _logger.error('Error while updating Peppol participant status: %s', e)
                continue

            if 'error' in proxy_user:
                error_message = proxy_user['error'].get('message') or proxy_user['error'].get('data', {}).get('message')
                _logger.error('Error while updating Peppol participant status: %s', error_message)
                continue

            local_state = {
                'draft': 'not_registered',
                'sender': 'sender',
                'smp_registration': 'smp_registration',
                'receiver': 'receiver',
                'rejected': 'rejected',
            }.get(proxy_user.get('peppol_state'))

            if local_state == 'not_registered':
                edi_user.sudo().company_id._reset_peppol_configuration()
                edi_user.action_archive()
            elif local_state:
                edi_user.company_id.account_peppol_proxy_state = local_state
            else:
                _logger.warning("Received unknown Peppol state '%s' for EDI proxy user id=%s", proxy_user.get('peppol_state'), edi_user.id)