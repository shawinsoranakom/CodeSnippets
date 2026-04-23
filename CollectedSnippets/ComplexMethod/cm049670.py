def _l10n_sa_get_csid_error(self, csid):
        """
            Return a formatted error string if the CSID response has an 'error' or 'errors'
            key or doesn't have a 'binarySecurityToken'
        """
        error_msg = ""
        unknown_error_msg = _("Unknown response returned from ZATCA. Please check the logs.")
        if error := csid.get('error'):
            error_msg = error
        elif errors := csid.get('errors'):
            error_msg = " <br/>" + " <br/>- ".join([err['message'] if isinstance(err, dict) else err for err in errors])
        elif 'error' in [csid.get('type', "").lower(), csid.get('status', "").lower()]:
            error_msg = csid.get('message') or unknown_error_msg
        elif not csid.get('binarySecurityToken'):
            error_msg = unknown_error_msg

        if error_msg:
            _logger.warning("Failed to obtain CSID: %s", csid)

        return error_msg