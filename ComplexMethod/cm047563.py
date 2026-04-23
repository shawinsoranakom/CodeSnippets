def _read_group_format_result(self, rows_dict, lazy_groupby):
        """
        Helper method to format the data contained in the dictionary data by
        adding the domain corresponding to its values, the groupbys in the
        context and by properly formatting the date/datetime values.
        """
        for group in lazy_groupby:
            field_name = group.split(':')[0].split('.')[0]
            field = self._fields[field_name]

            if field.type in ('date', 'datetime'):
                granularity = group.split(':')[1] if ':' in group else 'month'
                if granularity in READ_GROUP_TIME_GRANULARITY:
                    locale = get_lang(self.env).code
                    fmt = DEFAULT_SERVER_DATETIME_FORMAT if field.type == 'datetime' else DEFAULT_SERVER_DATE_FORMAT
                    interval = READ_GROUP_TIME_GRANULARITY[granularity]
            elif field.type == "properties":
                self._read_group_format_result_properties(rows_dict, group)
                continue

            for row in rows_dict:
                value = row[group]

                if isinstance(value, BaseModel):
                    row[group] = (value.id, value.sudo().display_name) if value else False
                    value = value.id

                if not value and field.type == 'many2many':
                    additional_domain = [(field_name, 'not any', [])]
                else:
                    additional_domain = [(field_name, '=', value)]

                if field.type in ('date', 'datetime'):
                    if value and isinstance(value, (datetime.date, datetime.datetime)):
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
                                tzinfo=tzinfo, locale=locale
                            )
                        else:
                            label = babel.dates.format_date(
                                value, format=READ_GROUP_DISPLAY_FORMAT[granularity],
                                locale=locale
                            )
                        # special case weeks because babel is broken *and*
                        # ubuntu reverted a change so it's also inconsistent
                        if granularity == 'week':
                            year, week = date_utils.weeknumber(
                                babel.Locale.parse(locale),
                                value,  # provide date or datetime without UTC conversion
                            )
                            label = f"W{week} {year:04}"

                        range_start = range_start.strftime(fmt)
                        range_end = range_end.strftime(fmt)
                        row[group] = label  # TODO should put raw data
                        row.setdefault('__range', {})[group] = {'from': range_start, 'to': range_end}
                        additional_domain = [
                            '&',
                                (field_name, '>=', range_start),
                                (field_name, '<', range_end),
                        ]
                    elif value is not None and granularity in READ_GROUP_NUMBER_GRANULARITY:
                        additional_domain = [(f"{field_name}.{granularity}", '=', value)]
                    elif not value:
                        # Set the __range of the group containing records with an unset
                        # date/datetime field value to False.
                        row.setdefault('__range', {})[group] = False

                row['__domain'] &= Domain(additional_domain)
        for row in rows_dict:
            row['__domain'] = list(row['__domain'])