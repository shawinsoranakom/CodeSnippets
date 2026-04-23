def attributes(self, record, field_name, options, values=None):
        attrs = super().attributes(record, field_name, options, values)
        if options.get('inherit_branding'):
            field = record._fields[field_name]
            if field.sanitize:
                if field.sanitize_overridable:
                    if record.env.user.has_group('base.group_sanitize_override'):
                        # Don't mark the field as 'sanitize' if the sanitize
                        # is defined as overridable and the user has the right
                        # to do so
                        return attrs
                    else:
                        try:
                            field.convert_to_column_insert(record[field_name], record)
                        except UserError:
                            # The field contains element(s) that would be
                            # removed if sanitized. It means that someone who
                            # was part of a group allowing to bypass the
                            # sanitation saved that field previously. Mark the
                            # field as not editable.
                            attrs['data-oe-sanitize-prevent-edition'] = 1
                            return attrs
                # The field edition is not fully prevented and the sanitation cannot be bypassed
                attrs['data-oe-sanitize'] = 'no_block' if field.sanitize_attributes else 1 if field.sanitize_form else 'allow_form'

        return attrs