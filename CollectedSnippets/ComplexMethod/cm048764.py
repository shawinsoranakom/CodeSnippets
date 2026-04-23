def _compute_display_name(self):
        type_tax_uses = dict(self._fields['type_tax_use']._description_selection(self.env))
        scopes = dict(self._fields['tax_scope']._description_selection(self.env))

        needs_markdown = self.env.context.get('formatted_display_name')
        wrapper = "\t--%s--" if needs_markdown else " (%s)"
        fields_to_include = set(self.env.context.get('append_fields') or [])

        for record in self:
            if name := record.name:
                if 'type_tax_use' in fields_to_include and (use := type_tax_uses.get(record.type_tax_use)):
                    name += wrapper % use
                if 'company_id' in fields_to_include and len(self.env.companies) > 1:
                    name += wrapper % record.company_id.display_name
                if needs_markdown and (scope := scopes.get(record.tax_scope)):  # scope is always in the dropdown options, never in the tag
                    name += wrapper % scope
                if record.country_id != record.company_id._accessible_branches()[:1].account_fiscal_country_id:
                    name += wrapper % record.country_code

            record.display_name = name