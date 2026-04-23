def button_nemhandel_registration_sms(self):
        """
        The first step of the Nemhandel onboarding.
        - Creates an EDI proxy user on the iap side, then the client side
        - Calls /activate_participant to mark the EDI user as nemhandel user
        - Sends an SMS code
        """
        self.ensure_one()

        if self.l10n_dk_nemhandel_proxy_state != 'not_registered':
            raise UserError(_('Cannot register a user with a %s application', self.l10n_dk_nemhandel_proxy_state))

        if not self.phone_number:
            raise ValidationError(_("Please enter a phone number to verify your application."))
        if not self.contact_email:
            raise ValidationError(_("Please enter a primary contact email to verify your application."))
        if not self.env.company.vat:
            raise RedirectWarning(
                _("Please fill in your company's VAT"),
                self.env.ref('base.action_res_company_form').id,
                _('Company settings')
            )

        if not self.edi_user_id:
            edi_user = self.edi_user_id.sudo()._register_proxy_user(self.company_id, 'nemhandel', self.edi_mode)
            self.edi_user_id = edi_user

            # if there is an error when activating the participant below,
            # the client side is rolled back and the edi user is deleted on the client side
            # but remains on the proxy side.
            # it is important to keep these two in sync, so commit before activating.
            if not modules.module.current_test:
                self.env.cr.commit()

        self.edi_user_id._check_user_on_alternative_service()

        if self.edi_user_id.edi_mode != 'demo':
            return self.send_nemhandel_verification_code()
        return self._action_open_nemhandel_form()