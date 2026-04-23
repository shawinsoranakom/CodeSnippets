def _get_user_from_token(self, token: str, url: str):
        try:
            if not (payload := tools.verify_hash_signed(self.sudo().env, 'account_peppol_webhook', token)):
                return None
        except ValueError:
            return None
        else:
            id, endpoint = payload
            if not url.startswith(endpoint):
                return None
            company = self.env['res.company'].browse(id).exists()
            if company and company.account_peppol_edi_user:
                return company.account_peppol_edi_user
            if edi_user := self.browse(id).exists():
                # Legacy fallback: we no longer generate the token based on the proxy_user, as it does
                # not exists yet with the new creation flow.
                # This can be safely removed after beginning of March 2026 (webhooks TTL = 30 days).
                return edi_user
            return None