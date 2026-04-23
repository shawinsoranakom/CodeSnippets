def set(self, model_name, field_name, value, user_id=False, company_id=False, condition=False):
        """ Defines a default value for the given field. Any entry for the same
            scope (field, user, company) will be replaced. The value is encoded
            in JSON to be stored to the database.

            :param model_name:
            :param field_name:
            :param value:
            :param user_id: may be ``False`` for all users, ``True`` for the
                            current user, or any user id
            :param company_id: may be ``False`` for all companies, ``True`` for
                               the current user's company, or any company id
            :param condition: optional condition that restricts the
                              applicability of the default value; this is an
                              opaque string, but the client typically uses
                              single-field conditions in the form ``'key=val'``.
        """
        if user_id is True:
            user_id = self.env.uid
        if company_id is True:
            company_id = self.env.company.id

        # check consistency of model_name, field_name, and value
        try:
            model = self.env[model_name]
            field = model._fields[field_name]
            parsed = field.convert_to_cache(value, model)
            if field.type in ('date', 'datetime') and isinstance(value, date):
                value = field.to_string(value)
            json_value = json.dumps(value, ensure_ascii=False)
        except KeyError:
            raise ValidationError(self.env._("Invalid field %(model)s.%(field)s", model=model_name, field=field_name))
        except Exception:
            raise ValidationError(self.env._("Invalid value for %(model)s.%(field)s: %(value)s", model=model_name, field=field_name, value=value))
        if field.type == 'integer' and not (-2**31 < parsed < 2**31-1):
            raise ValidationError(self.env._("Invalid value for %(model)s.%(field)s: %(value)s is out of bounds (integers should be between -2,147,483,648 and 2,147,483,647)", model=model_name, field=field_name, value=value))

        # update existing default for the same scope, or create one
        field = self.env['ir.model.fields']._get(model_name, field_name)
        default = self.search([
            ('field_id', '=', field.id),
            ('user_id', '=', user_id),
            ('company_id', '=', company_id),
            ('condition', '=', condition),
        ], limit=1)
        if default:
            # Avoid clearing the cache if nothing changes
            if default.json_value != json_value:
                default.write({'json_value': json_value})
        else:
            self.create({
                'field_id': field.id,
                'user_id': user_id,
                'company_id': company_id,
                'condition': condition,
                'json_value': json_value,
            })
        return True