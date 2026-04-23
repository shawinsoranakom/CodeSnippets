def _onchange_company_id(self):
        for wizard in self:
            wizard.logo = wizard.company_id.logo
            wizard.report_header = wizard.company_id.report_header
            # company_details and report_footer can store empty strings (set by the user) or false (meaning the user didn't set a value). Since both are falsy values, we use isinstance of string to differentiate them
            wizard.report_footer = wizard.company_id.report_footer if isinstance(wizard.company_id.report_footer, str) else wizard.report_footer
            wizard.company_details = wizard.company_id.company_details if isinstance(wizard.company_id.company_details, str) else wizard.company_details
            wizard.paperformat_id = wizard.company_id.paperformat_id
            wizard.external_report_layout_id = wizard.company_id.external_report_layout_id
            wizard.font = wizard.company_id.font
            wizard.primary_color = wizard.company_id.primary_color
            wizard.secondary_color = wizard.company_id.secondary_color
            wizard_layout = wizard.env["report.layout"].search([
                ('view_id.key', '=', wizard.company_id.external_report_layout_id.key)
            ])
            wizard.report_layout_id = wizard_layout or wizard_layout.search([], limit=1)

            if not wizard.primary_color:
                wizard.primary_color = wizard.logo_primary_color or DEFAULT_PRIMARY
            if not wizard.secondary_color:
                wizard.secondary_color = wizard.logo_secondary_color or DEFAULT_SECONDARY