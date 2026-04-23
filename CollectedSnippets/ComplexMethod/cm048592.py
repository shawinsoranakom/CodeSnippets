def _pre_load_data(self, template_code, company, template_data, data):
        """Pre-process the data and preload some values.

        Some of the data needs special pre_process before being fed to the database.
        e.g. the account codes' width must be standardized to the code_digits applied.
        The fiscal country code must be put in place before taxes are generated.
        """
        if 'account_fiscal_country_id' in data.get('res.company', {}).get(company.id, {}):
            fiscal_country = self.ref(data['res.company'][company.id]['account_fiscal_country_id'])
        else:
            fiscal_country = company.account_fiscal_country_id

        # Apply template data to the company
        filter_properties = lambda key: (
            (not key.startswith("property_") or key.startswith("property_stock_") or key == "additional_properties")
            and key != 'name'
            and key in company._fields
        )

        # Set the currency to the fiscal country's currency
        vals = {key: val for key, val in template_data.items() if filter_properties(key)}
        if not company.root_id._existing_accounting():
            if company.parent_id:
                vals['currency_id'] = company.parent_id.currency_id.id
            else:
                vals['currency_id'] = fiscal_country.currency_id.id
        if not company.country_id:
            vals['country_id'] = fiscal_country.id

        # Ensure that we write on 'anglo_saxon_accounting' when changing to a CoA that relies on the default of `False`.
        vals.setdefault('anglo_saxon_accounting', False)

        # This write method is important because it's overridden and has additional triggers
        # e.g it activates the currency
        company.write(vals)

        # Normalize the code_digits of the accounts
        code_digits = int(template_data.get('code_digits', 6))
        for key, account_data in data.get('account.account', {}).items():
            if 'code' in account_data:
                data['account.account'][key]['code'] = f'{account_data["code"]:<0{code_digits}}'

        for model in ('account.fiscal.position', 'account.reconcile.model'):
            if model in data:
                data[model] = data.pop(model)

        # Exclude data of unknown fields present in the template
        if not self.env.context.get('l10n_check_fields_complete'):
            for model_name, records in data.items():
                for record in records.values():
                    keys_to_delete = []
                    for key in record:
                        if key == '__translation_module__':
                            continue

                        fname = key.split('@')[0] if '@' in key else key
                        if fname not in self.env[model_name]._fields:
                            keys_to_delete.append(key)
                    for key in keys_to_delete:
                        del record[key]

        # Translate the untranslatable fields we want to translate anyway
        untranslatable_model_fields = self._get_untranslatable_fields_to_translate()
        untranslatable_target_lang = self._get_untranslatable_fields_target_language(template_code, company)
        for model_name, records in data.items():
            untranslatable_fields = untranslatable_model_fields.get(model_name, [])
            if not untranslatable_fields:
                continue
            for record in records.values():
                for field in untranslatable_fields:
                    if field not in record:
                        continue
                    translation = self._get_field_translation(record, field, untranslatable_target_lang)
                    if translation:
                        record[field] = translation

        return data