def _l10n_in_edi_strict_error_validation(self):
        """
        This method is used to check the strict validation of the partner data
        as per government API json schema (https://einv-apisandbox.nic.in/version1.03/generate-irn.html#requestSampleJSON)
        In case of any error, it will return the error message
        Note - We stimulate as error message from API, so that user can understand the error
        Also restrict unwanted request to government servers and avoid getting black listed
        """
        message = []
        if not re.match("^.{3,100}$", self.street or ""):
            message.append(_("- Street required min 3 and max 100 characters"))
        if not re.match("^.{3,100}$", self.city or ""):
            message.append(_("- City required min 3 and max 100 characters"))
        if self.country_id.code == "IN" and not re.match("^.{3,50}$", self.state_id.name or ""):
            message.append(_("- State required min 3 and max 50 characters"))
        if self.country_id.code == "IN" and not re.match("^([1-9][0-9]{5})$", self.zip or ""):
            message.append(_("- ZIP code required 6 digits ranging from 100000 to 999999"))
        if (
            self.country_id.code == "IN"
            and not re.match(r"^(?!0+$)([0-9]{2})$", self.state_id.l10n_in_tin or "")
        ):
            message.append(_("- State TIN Number must be exactly 2 digits."))
        if message:
            message.insert(0, self.display_name)
        return message