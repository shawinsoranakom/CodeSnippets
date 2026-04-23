def _ensure_can_connect(self, can_connect_vals, selected_auth=None):
        """Checks the answer from the /can_connect endpoint and raises an error if it's invalid."""
        if not can_connect_vals:
            raise UserError(_("Could not connect to Proxy Server."))
        if identifier_invalid := can_connect_vals.get('identifier_invalid'):
            if identifier_invalid.get('code') == 'IDENTIFIER_NOT_ON_PEPPOL':
                raise UserError(_("Your identifier you entered is invalid for Peppol."))
            if identifier_invalid.get('code') == 'IDENTIFIER_INCORRECT_FORMAT':
                example = _(" Expected format: %(expected_format)s.", identifier_invalid['example']) if identifier_invalid.get('example') else ""
                raise UserError(_("Your identifier does not have a valid format.%s", example))
            raise UserError(_("Your identifier is invalid."))
        if can_connect_vals.get('db_invalid'):
            raise UserError(_("The database you are trying to connect to is not suitable for Peppol."))
        if not selected_auth and can_connect_vals.get('auth_required'):
            raise UserError(_("You need to authenticate to continue."))
        if selected_auth and not can_connect_vals.get('available_auths', {}).get(selected_auth):
            raise UserError(_("Selected authentication method is not available."))