def _import_ubl_invoice_retrieve_taxes(self, collected_values):
        company = collected_values['company']
        logs = collected_values['logs']
        lines_collected_values = collected_values['lines_collected_values']
        tax_values_list = list(collected_values['taxes_values'])
        for line_collected_values in lines_collected_values:
            tax_values_list += line_collected_values['taxes_values']
            for charge in line_collected_values['charges']:
                if tax_values := charge.get('attempt_tax_values'):
                    tax_values_list.append(tax_values)

        self.env['account.tax']._import_retrieve_tax(
            search_plan=self._import_ubl_retrieve_taxes_search_plan(collected_values),
            company=company,
            tax_values_list=tax_values_list,
        )

        # Taxes at the document line level.
        for line_collected_values in lines_collected_values:
            to_write = line_collected_values['to_write']
            tax_ids_commands = to_write['tax_ids'] = [Command.set([])]
            for tax_values in line_collected_values['taxes_values']:
                if tax := tax_values.get('tax'):
                    tax_ids_commands[0][2].append(tax.id)
                elif reason := tax_values.get('name'):
                    logs.append(_(
                        "Could not retrieve the tax: %(tax_percentage)s %% for line '%(line)s'.",
                        tax_percentage=tax_values['amount'],
                        line=reason,
                    ))
                else:
                    logs.append(_(
                        "Could not retrieve the tax: %s for the document level allowance/charge.",
                        tax_values['amount'],
                    ))

        # Taxes at the document level.
        for tax_values in collected_values['taxes_values']:
            if tax_values.get('tax'):
                continue

            if reason := tax_values.get('name'):
                logs.append(_(
                    "Could not retrieve the tax: %(tax_percentage)s %% for line '%(line)s'.",
                    tax_percentage=tax_values['amount'],
                    line=reason,
                ))
            else:
                logs.append(_(
                    "Could not retrieve the tax: %s for the document level allowance/charge.",
                    tax_values['amount'],
                ))