def _l10n_in_edi_optional_field_validation(self, partner):
        """
        Validates optional partner fields (e.g., email, phone, street2) for e-invoicing,
        which are not mandatory in the government API JSON schema. Returns error messages
        for posting in the chatter.
        """
        message = []
        if partner.email and (
            not re.match(r"^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$", partner.email) or
            not re.match(r"^.{6,100}$", partner.email)
        ):
            message.append(_("- Email: invalid or longer than 100 characters."))
        if partner.phone and not re.match(
            r"^[0-9]{10,12}$",
            partner.env['account.move']._l10n_in_extract_digits(partner.phone)
        ):
            message.append(_("- Phone number: must be 10–12 digits."))
        if partner.street2 and not re.match(r"^.{3,100}$", partner.street2):
            message.append(_("- Street2: must be 3–100 characters."))
        return message