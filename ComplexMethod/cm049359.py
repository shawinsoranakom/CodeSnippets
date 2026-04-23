def _get_and_cache_current_fiscal_position(self):
        """Retrieve and cache the current fiscal position for the session.

        Note: self.ensure_one()

        :return: A sudoed fiscal position record.
        :rtype: account.fiscal.position
        """
        self.ensure_one()

        AccountFiscalPositionSudo = self.env['account.fiscal.position'].sudo()
        fpos_sudo = AccountFiscalPositionSudo

        if FISCAL_POSITION_SESSION_CACHE_KEY in request.session:
            fpos_sudo = AccountFiscalPositionSudo.browse(
                request.session[FISCAL_POSITION_SESSION_CACHE_KEY]
            )
            if fpos_sudo and fpos_sudo.exists():
                return fpos_sudo

        partner_sudo = self.env.user.partner_id

        # If the current user is the website public user, the fiscal position
        # is computed according to geolocation.
        if request and request.geoip.country_code and self.partner_id.id == partner_sudo.id:
            country = self.env['res.country'].search(
                [('code', '=', request.geoip.country_code)],
                limit=1,
            )
            partner_geoip = self.env['res.partner'].sudo().new({'country_id': country.id})
            fpos_sudo = AccountFiscalPositionSudo._get_fiscal_position(partner_geoip)

        if not fpos_sudo:
            fpos_sudo = AccountFiscalPositionSudo._get_fiscal_position(partner_sudo)

        request.session[FISCAL_POSITION_SESSION_CACHE_KEY] = fpos_sudo.id

        return fpos_sudo