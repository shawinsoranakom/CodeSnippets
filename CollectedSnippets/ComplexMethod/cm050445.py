def _check_spreadsheet_data(self):
        for spreadsheet in self.filtered("spreadsheet_binary_data"):
            try:
                data = json.loads(base64.b64decode(spreadsheet.spreadsheet_binary_data).decode())
            except (json.JSONDecodeError, UnicodeDecodeError):
                raise ValidationError(_("Uh-oh! Looks like the spreadsheet file contains invalid data."))
            if not (tools.config['test_enable'] or tools.config['test_file']):
                continue
            if data.get("[Content_Types].xml"):
                # this is a xlsx file
                continue
            display_name = spreadsheet.display_name
            errors = []
            for model, field_chains in fields_in_spreadsheet(data).items():
                if model not in self.env:
                    errors.append(f"- model '{model}' used in '{display_name}' does not exist")
                    continue
                for field_chain in field_chains:
                    field_model = model
                    for fname in field_chain.split("."):  # field chain 'product_id.channel_ids'
                        if fname not in self.env[field_model]._fields:
                            errors.append(f"- field '{fname}' used in spreadsheet '{display_name}' does not exist on model '{field_model}'")
                            continue
                        field = self.env[field_model]._fields[fname]
                        if field.relational:
                            field_model = field.comodel_name

            for xml_id in menus_xml_ids_in_spreadsheet(data):
                record = self.env.ref(xml_id, raise_if_not_found=False)
                if not record:
                    errors.append(f"- xml id '{xml_id}' used in spreadsheet '{display_name}' does not exist")
                    continue
                # check that the menu has an action. Root menus always have an action.
                if not record.action and record.parent_id.id:
                    errors.append(f"- menu with xml id '{xml_id}' used in spreadsheet '{display_name}' does not have an action")

            if errors:
                raise ValidationError(
                    _(
                        "Uh-oh! Looks like the spreadsheet file contains invalid data.\n\n%(errors)s",
                        errors="\n".join(errors),
                    ),
                )