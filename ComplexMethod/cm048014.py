def _ensure_mandatory_fields(self):
        if not self.selected_company_id.account_fiscal_country_id.code:
            raise ValidationError(_("Please select a country for your company."))
        if not self.contact_email or not self.phone_number:
            raise ValidationError(_("Contact email and phone number are required."))
        if not self.peppol_eas or not self.peppol_endpoint:
            raise ValidationError(_("Peppol Address should be provided."))
        if self._branch_with_same_address():
            raise ValidationError(_("Peppol ID should be different from main company."))
        if self.company_id.account_peppol_proxy_state != 'not_registered':
            raise ValidationError(_("Cannot register a user with a %s application", self.account_peppol_proxy_state))