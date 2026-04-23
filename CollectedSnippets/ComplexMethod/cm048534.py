def _compute_sending_method_checkboxes(self):
        """ Select one applicable sending method given the following priority
        1. preferred method set on partner,
        2. email,
        """
        methods = self.env['ir.model.fields'].get_field_selection('res.partner', 'invoice_sending_method')

        # We never want to display the manual method.
        methods = [method for method in methods if method[0] != 'manual']

        for wizard in self:
            preferred_methods = self._get_default_sending_methods(wizard.move_id)
            wizard.sending_method_checkboxes = {
                method_key: {
                    'checked': (
                        method_key in preferred_methods and (
                            method_key == 'email' or self._is_applicable_to_move(method_key, wizard.move_id, **self._get_default_sending_settings(wizard.move_id))
                        )),  # email method is always ok in single mode since the email can be added if it's missing
                    'label': method_label,
                }
                for method_key, method_label in methods
                if self._is_applicable_to_company(method_key, wizard.company_id)
            }