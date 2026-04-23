def _web_read_group_groupby_formatter(self, groupby_spec, values):
        """ Return a formatter method that returns value/label and the domain that the group
        value represent """
        field_path = groupby_spec.split(':')[0]
        field_name, _dot, remaining_path = field_path.partition('.')
        field = self._fields[field_name]

        if remaining_path and field.type == 'many2one':
            model = self.env[field.comodel_name]
            sub_formatter = model._web_read_group_groupby_formatter(groupby_spec.split('.', 1)[1], values)

            def formatter_follow_many2one(value):
                value, domain = sub_formatter(value)
                if not value:
                    return value, ['|', (field_name, 'not any', []), (field_name, 'any', domain)]
                return value, [(field_name, 'any', domain)]

            return formatter_follow_many2one

        if field.type == 'many2many':

            # Special case for many2many because (<many2many>, '=', False) domain bypass ir.rule.
            def formatter_many2many(value):
                if not value:
                    return False, [(field_name, 'not any', [])]
                id_ = value.id
                return (id_, value.sudo().display_name), [(field_name, '=', id_)]

            return formatter_many2many

        if field.type == 'many2one' or field_name == 'id':

            def formatter_many2one(value):
                if not value:
                    return False, [(field_name, '=', False)]
                id_ = value.id
                return (id_, value.sudo().display_name), [(field_name, '=', id_)]

            return formatter_many2one

        if field.type in ('date', 'datetime'):
            assert ':' in groupby_spec, "Granularity is missing"
            granularity = groupby_spec.split(':')[1]
            if granularity in READ_GROUP_TIME_GRANULARITY:
                locale = get_lang(self.env).code
                fmt = DEFAULT_SERVER_DATETIME_FORMAT if field.type == 'datetime' else DEFAULT_SERVER_DATE_FORMAT
                interval = READ_GROUP_TIME_GRANULARITY[granularity]

                def formatter_time_granularity(value):
                    if not value:
                        return value, [(field_name, '=', value)]
                    range_start = value
                    range_end = value + interval
                    if field.type == 'datetime':
                        tzinfo = None
                        if self.env.context.get('tz') in pytz.all_timezones_set:
                            tzinfo = pytz.timezone(self.env.context['tz'])
                            range_start = tzinfo.localize(range_start).astimezone(pytz.utc)
                            # take into account possible hour change between start and end
                            range_end = tzinfo.localize(range_end).astimezone(pytz.utc)

                        label = babel.dates.format_datetime(
                            range_start, format=READ_GROUP_DISPLAY_FORMAT[granularity],
                            tzinfo=tzinfo, locale=locale,
                        )
                    else:
                        label = babel.dates.format_date(
                            value, format=READ_GROUP_DISPLAY_FORMAT[granularity],
                            locale=locale,
                        )

                    # special case weeks because babel is broken *and*
                    # ubuntu reverted a change so it's also inconsistent
                    if granularity == 'week':
                        year, week = date_utils.weeknumber(
                            babel.Locale.parse(locale),
                            value,  # provide date or datetime without UTC conversion
                        )
                        label = f"W{week} {year:04}"

                    additional_domain = ['&',
                        (field_name, '>=', range_start.strftime(fmt)),
                        (field_name, '<', range_end.strftime(fmt)),
                    ]
                    # TODO: date label should be created by the webclient.
                    return (range_start.strftime(fmt), label), additional_domain

                return formatter_time_granularity

            if granularity in READ_GROUP_NUMBER_GRANULARITY:

                def formatter_date_number_granularity(value):
                    if value is None:
                        return [(field_name, '=', value)]
                    return value, [(f"{field_name}.{granularity}", '=', value)]

                return formatter_date_number_granularity

            raise ValueError(f"{granularity!r} isn't a valid granularity")

        if field.type == "properties":
            return self._web_read_group_groupby_properties_formatter(groupby_spec, values)

        return lambda value: (value, [(field_name, '=', value)])