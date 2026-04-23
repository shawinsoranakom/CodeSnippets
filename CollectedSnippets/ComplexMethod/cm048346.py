def _l10n_in_validate_partner(self, partner):
        """
        Validation method for Ewaybill (different from EDI)
        """
        message = []
        if partner.country_id.code == "IN":
            if partner.state_id and not partner.state_id.l10n_in_tin:
                message.append(_("- TIN number not set in state %s", partner.state_id.name))
            if not partner.state_id:
                message.append(_("- State is required"))
            if not partner.zip or not re.match("^[0-9]{6}$", partner.zip):
                message.append(_("- Zip code required and should be 6 digits"))
        elif not partner.country_id:
            message.append(_("- Country is required"))
        if message:
            message.insert(0, "%s" % partner.display_name)
        return message