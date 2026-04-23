def _parse_import_data_recursive(self, model, prefix, data, import_fields, options):
        # Get fields of type date/datetime
        all_fields = self.env[model].fields_get()
        for name, field in all_fields.items():
            name = prefix + name
            if field['type'] in ('date', 'datetime') and name in import_fields:
                index = import_fields.index(name)
                self._parse_date_from_data(data, index, name, field['type'], options)
            # Check if the field is in import_field and is a relational (followed by /)
            # Also verify that the field name exactly match the import_field at the correct level.
            elif any(name + '/' in import_field and name == import_field.split('/')[prefix.count('/')] for import_field in import_fields):
                # Recursive call with the relational as new model and add the field name to the prefix
                self._parse_import_data_recursive(field['relation'], name + '/', data, import_fields, options)
            elif field['type'] in ('float', 'monetary') and name in import_fields:
                # Parse float, sometimes float values from file have currency symbol or () to denote a negative value
                # We should be able to manage both case
                index = import_fields.index(name)
                self._parse_float_from_data(data, index, name, options)
            elif field['type'] == 'binary' and field.get('attachment') and name in import_fields:
                index = import_fields.index(name)

                import requests  # noqa: PLC0415
                with requests.Session() as session:
                    session.stream = True

                    for num, line in enumerate(data):
                        if re.match(config.get("import_url_regex"), line[index]):
                            if not self.env.user._can_import_remote_urls():
                                raise ImportValidationError(
                                    _("You can not import file via URL, check with your administrator or support for the reason."),
                                    field=name, field_type=field['type']
                                )
                            line[index] = self._import_file_by_url(line[index], session, name, num)
                        elif '.' in line[index]:
                            # Detect if it's a filename
                            pass
                        else:
                            try:
                                base64.b64decode(line[index], validate=True)
                            except ValueError:
                                raise ImportValidationError(
                                    _("Found invalid image data, images should be imported as either URLs or base64-encoded data."),
                                    field=name, field_type=field['type']
                                )

        return data