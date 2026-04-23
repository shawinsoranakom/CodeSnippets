def _find_value_from_field_path(self, field_path):
        """Get the value of field, returning display_name(s) if the field is a
        model. Can be called on a void recordset, in which case it mainly serves
        as a field path validation."""
        if self:
            self.ensure_one()

        # as we use mapped(False) returns record, better return a void string
        if not field_path:
            return ''

        try:
            field_value = self.mapped(field_path)
        except KeyError:
            raise exceptions.UserError(
                _("%(model_name)s.%(field_path)s does not seem to be a valid field path", model_name=self._name, field_path=field_path)
            )
        except Exception as err:  # noqa: BLE001
            raise exceptions.UserError(
                _("We were not able to fetch value of field '%(field)s'", field=field_path)
            ) from err
        if isinstance(field_value, models.Model):
            return ' '.join((value.display_name or '') for value in field_value)
        if any(isinstance(value, datetime) for value in field_value):
            tz = (self and self._mail_get_timezone()) or self.env.user.tz or 'UTC'
            return ' '.join([f"{tools.format_datetime(self.env, value, tz=tz)} {tz}"
                             for value in field_value if value and isinstance(value, datetime)])
        # find last field / last model when having chained fields
        # e.g. 'partner_id.country_id.state' -> ['partner_id.country_id', 'state']
        field_path_models = field_path.rsplit('.', 1)
        if len(field_path_models) > 1:
            last_model_path, last_fname = field_path_models
            last_model = self.mapped(last_model_path)
        else:
            last_model, last_fname = self, field_path
        last_field = last_model._fields[last_fname]
        # if selection -> return value, not the key
        if last_field.type == 'selection':
            return ' '.join(
                last_field.convert_to_export(value, last_model)
                for value in field_value
            )
        return ' '.join(str(value if value is not False and value is not None else '') for value in field_value)