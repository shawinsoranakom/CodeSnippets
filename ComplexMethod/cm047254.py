def _str_to_properties(self, model, field, value, savepoint):

        # If we want to import the all properties at once (with the technical value)
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except ValueError:
                msg = self.env._("Unable to import'%%(field)s' Properties field as a whole, target individual property instead.")
                raise self._format_import_error(ValueError, msg)

        if not isinstance(value, list):
            msg = self.env._("Unable to import'%%(field)s' Properties field as a whole, target individual property instead.")
            raise self._format_import_error(ValueError, msg, {'value': value})

        warnings = []
        for property_dict in value:
            if not (property_dict.keys() >= {'name', 'type', 'string'}):
                msg = self.env._("'%(value)s' does not seem to be a valid Property value for field '%%(field)s'. Each property need at least 'name', 'type' and 'string' attribute.")
                raise self._format_import_error(ValueError, msg, {'value': property_dict})

            val = property_dict.get('value')
            if not val:
                continue

            property_type = property_dict['type']

            if property_type == 'selection':
                # either label or the technical value
                new_val = next(iter(
                    sel_val for sel_val, sel_label in property_dict['selection']
                    if val in (sel_val, sel_label)
                ), None)
                if not new_val:
                    msg = self.env._("'%(value)s' does not seem to be a valid Selection value for '%(label_property)s' (subfield of '%%(field)s' field).")
                    raise self._format_import_error(ValueError, msg, {'value': val, 'label_property': property_dict['string']})
                property_dict['value'] = new_val

            elif property_type == 'tags':
                tags = val.split(',')
                new_val = []
                for tag in tags:
                    val_tag = next(iter(
                        tag_val for tag_val, tag_label, _color in property_dict['tags']
                        if tag in (tag_val, tag_label)
                    ), None)
                    if not val_tag:
                        msg = self.env._("'%(value)s' does not seem to be a valid Tag value for '%(label_property)s' (subfield of '%%(field)s' field).")
                        raise self._format_import_error(ValueError, msg, {'value': tag, 'label_property': property_dict['string']})
                    new_val.append(val_tag)
                property_dict['value'] = new_val

            elif property_type == 'boolean':
                new_val, warnings = self._str_to_boolean(model, field, val, savepoint=savepoint)
                if not warnings:
                    property_dict['value'] = new_val
                else:
                    msg = self.env._("Unknown value '%(value)s' for boolean '%(label_property)s' property (subfield of '%%(field)s' field).")
                    raise self._format_import_error(ValueError, msg, {'value': val, 'label_property': property_dict['string']})

            elif property_type in ('many2one', 'many2many'):
                [record] = property_dict['value']

                subfield, w1 = self._referencing_subfield(record)
                if w1:
                    warnings.append(w1)

                values = record[subfield]

                references = values.split(',') if property_type == 'many2many' else [values]
                ids = []
                fake_field = FakeField(comodel_name=property_dict['comodel'], name=property_dict['string'])
                for reference in references:
                    id_, ws = self.db_id_for(model, fake_field, subfield, reference, savepoint)
                    ids.append(id_)
                    warnings.extend(ws)

                property_dict['value'] = ids if property_type == 'many2many' else ids[0]

            elif property_type == 'integer':
                try:
                    property_dict['value'] = int(val)
                except ValueError:
                    msg = self.env._("'%(value)s' does not seem to be an integer for field '%(label_property)s' property (subfield of '%%(field)s' field).")
                    raise self._format_import_error(ValueError, msg, {'value': val, 'label_property': property_dict['string']})

            elif property_type == 'float':
                try:
                    property_dict['value'] = float(val)
                except ValueError:
                    msg = self.env._("'%(value)s' does not seem to be an float for field '%(label_property)s' property (subfield of '%%(field)s' field).")
                    raise self._format_import_error(ValueError, msg, {'value': val, 'label_property': property_dict['string']})

        return value, warnings