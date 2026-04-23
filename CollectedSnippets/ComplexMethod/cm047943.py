def _extract_binary_filenames(self, import_fields, data, model=False, prefix='', binary_filenames=False):
        model = model or self.res_model
        binary_filenames = binary_filenames or defaultdict(list)
        for name, field in self.env[model]._fields.items():
            name = prefix + name
            if any(name + '/' in import_field and name == import_field.split('/')[prefix.count('/')] for import_field in import_fields):
                # Recursive call with the relational as new model and add the field name to the prefix
                binary_filenames = self._extract_binary_filenames(import_fields, data, field.comodel_name, name + '/', binary_filenames)
            elif field.type == 'binary' and field.attachment and name in import_fields:
                index = import_fields.index(name)
                for line in data:
                    filename = None
                    value = line[index]
                    if isinstance(value, str):
                        if re.match(config.get("import_url_regex"), value):
                            pass
                        elif '.' in value:
                            # Detect if it's a filename
                            filename = value
                            line[index] = ''
                        # else base64 nothing to do
                    binary_filenames[name].append(filename)
        return binary_filenames