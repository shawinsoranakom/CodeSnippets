def _web_read_group_groupby_properties_formatter(self, groupby_spec, values):
        if '.' not in groupby_spec:
            raise ValueError('You must choose the property you want to group by.')

        fullname, __, func = groupby_spec.partition(':')
        definition = self.get_property_definition(fullname)
        property_type = definition.get('type')
        if property_type == 'selection':
            options = definition.get('selection') or []
            options = tuple(option[0] for option in options)

            def formatter_property_selection(value):
                if not value:
                    # can not do ('selection', '=', False) because we might have
                    # option in database that does not exist anymore
                    return value, ['|', (fullname, '=', False), (fullname, 'not in', options)]
                return value, [(fullname, '=', value)]

            return formatter_property_selection

        if property_type == 'many2one':
            comodel = definition['comodel']
            all_groups = tuple(value for value in values if value)

            def formatter_property_many2one(value):
                if not value:
                    # can not only do ('many2one', '=', False) because we might have
                    # record in database that does not exist anymore
                    return value, ['|', (fullname, '=', False), (fullname, 'not in', all_groups)]
                record = self.env[comodel].browse(value).with_prefetch(all_groups)
                return (value, record.display_name), [(fullname, '=', value)]

            return formatter_property_many2one

        if property_type == 'many2many':
            comodel = definition['comodel']
            all_groups = tuple(value for value in values if value)

            def formatter_property_many2many(value):
                if not value:
                    return value, OR([
                        [(fullname, '=', False)],
                        AND([[(fullname, 'not in', group)] for group in all_groups]),
                    ]) if all_groups else []
                record = self.env[comodel].browse(value).with_prefetch(all_groups)
                return (value, record.display_name), [(fullname, 'in', value)]

            return formatter_property_many2many

        if property_type == 'tags':
            tags = definition.get('tags') or []
            tags = {tag[0]: tuple(tag) for tag in tags}

            def formatter_property_tags(value):
                if not value:
                    return value, OR([
                        [(fullname, '=', False)],
                        AND([[(fullname, 'not in', tag)] for tag in tags]),
                    ]) if tags else []

                # replace tag raw value with tuple of raw value, label and color
                return tags.get(value), [(fullname, 'in', value)]

            return formatter_property_tags

        if property_type in ('date', 'datetime'):

            def formatter_property_datetime(value):
                if not value:
                    return False, [(fullname, '=', False)]

                # Date / Datetime are not JSONifiable, so they are stored as raw text
                db_format = '%Y-%m-%d' if property_type == 'date' else '%Y-%m-%d %H:%M:%S'
                fmt = DEFAULT_SERVER_DATE_FORMAT if property_type == 'date' else DEFAULT_SERVER_DATETIME_FORMAT

                if func == 'week':
                    # the value is the first day of the week (based on local)
                    start = value.strftime(db_format)
                    end = (value + datetime.timedelta(days=7)).strftime(db_format)
                else:
                    start = (date_utils.start_of(value, func)).strftime(db_format)
                    end = (date_utils.end_of(value, func) + datetime.timedelta(minutes=1)).strftime(db_format)

                label = babel.dates.format_date(
                    value,
                    format=READ_GROUP_DISPLAY_FORMAT[func],
                    locale=get_lang(self.env).code,
                )
                return (value.strftime(fmt), label), [(fullname, '>=', start), (fullname, '<', end)]

            return formatter_property_datetime

        return lambda value: (value, [(fullname, '=', value)])