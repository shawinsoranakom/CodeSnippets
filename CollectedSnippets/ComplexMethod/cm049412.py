def default_get(self, fields):
        values = super(UtmMixin, self).default_get(fields)

        # We ignore UTM for salesmen, except some requests that could be done as superuser_id to bypass access rights.
        if not self.env.is_superuser() and self.env.user.has_group('sales_team.group_sale_salesman'):
            return values

        for _url_param, field_name, cookie_name in self.env['utm.mixin'].tracking_fields():
            if field_name in fields:
                field = self._fields[field_name]
                value = False
                if request:
                    # ir_http dispatch saves the url params in a cookie
                    value = request.cookies.get(cookie_name)
                # if we receive a string for a many2one, we search/create the id
                if field.type == 'many2one' and isinstance(value, str) and value:
                    record = self._find_or_create_record(field.comodel_name, value)
                    value = record.id
                if value:
                    values[field_name] = value
        return values