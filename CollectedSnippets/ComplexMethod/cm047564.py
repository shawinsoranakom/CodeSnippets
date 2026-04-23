def _read_group_format_result_properties(self, rows_dict, group):
        """Modify the final read group properties result.

        Replace the relational properties ids by a tuple with their display names,
        replace the "raw" tags and selection values by a list containing their labels.
        Adapt the domains for the Falsy group (we can't just keep (selection, =, False)
        e.g. because some values in database might correspond to  option that have
        been remove on the parent).
        """
        if '.' not in group:
            raise ValueError('You must choose the property you want to group by.')
        fullname, __, func = group.partition(':')

        definition = self.get_property_definition(fullname)
        property_type = definition.get('type')

        if property_type == 'selection':
            options = definition.get('selection') or []
            options = tuple(option[0] for option in options)
            for row in rows_dict:
                if not row[fullname]:
                    # can not do ('selection', '=', False) because we might have
                    # option in database that does not exist anymore
                    additional_domain = Domain(fullname, '=', False) | Domain(fullname, 'not in', options)
                else:
                    additional_domain = Domain(fullname, '=', row[fullname])

                row['__domain'] &= additional_domain

        elif property_type == 'many2one':
            comodel = definition.get('comodel')
            prefetch_ids = tuple(row[fullname] for row in rows_dict if row[fullname])
            all_groups = tuple(row[fullname] for row in rows_dict if row[fullname])
            for row in rows_dict:
                if not row[fullname]:
                    # can not only do ('many2one', '=', False) because we might have
                    # record in database that does not exist anymore
                    additional_domain = Domain(fullname, '=', False) | Domain(fullname, 'not in', all_groups)
                else:
                    additional_domain = Domain(fullname, '=', row[fullname])
                    record = self.env[comodel].browse(row[fullname]).with_prefetch(prefetch_ids)
                    row[fullname] = (row[fullname], record.display_name)

                row['__domain'] &= additional_domain

        elif property_type == 'many2many':
            comodel = definition.get('comodel')
            prefetch_ids = tuple(row[fullname] for row in rows_dict if row[fullname])
            all_groups = tuple(row[fullname] for row in rows_dict if row[fullname])
            for row in rows_dict:
                if not row[fullname]:
                    if all_groups:
                        additional_domain = Domain(fullname, '=', False) | Domain.AND([(fullname, 'not in', group)] for group in all_groups)
                    else:
                        additional_domain = Domain.TRUE
                else:
                    additional_domain = Domain(fullname, 'in', row[fullname])
                    record = self.env[comodel].browse(row[fullname]).with_prefetch(prefetch_ids)
                    row[fullname] = (row[fullname], record.display_name)

                row['__domain'] &= additional_domain

        elif property_type == 'tags':
            tags = definition.get('tags') or []
            tags = {tag[0]: tag for tag in tags}
            for row in rows_dict:
                if not row[fullname]:
                    if tags:
                        additional_domain = Domain(fullname, '=', False) | Domain.AND([(fullname, 'not in', tag)] for tag in tags)
                    else:
                        additional_domain = Domain.TRUE
                else:
                    additional_domain = Domain(fullname, 'in', row[fullname])
                    # replace tag raw value with list of raw value, label and color
                    row[fullname] = tags.get(row[fullname])

                row['__domain'] &= additional_domain

        elif property_type in ('date', 'datetime'):
            for row in rows_dict:
                if not row[group]:
                    row[group] = False
                    row['__domain'] &= Domain(fullname, '=', False)
                    row['__range'] = {}
                    continue

                # Date / Datetime are not JSONifiable, so they are stored as raw text
                db_format = '%Y-%m-%d' if property_type == 'date' else '%Y-%m-%d %H:%M:%S'

                if func == 'week':
                    # the value is the first day of the week (based on local)
                    start = row[group].strftime(db_format)
                    end = (row[group] + datetime.timedelta(days=7)).strftime(db_format)
                else:
                    start = (date_utils.start_of(row[group], func)).strftime(db_format)
                    end = (date_utils.end_of(row[group], func) + datetime.timedelta(minutes=1)).strftime(db_format)

                row['__domain'] &= Domain(fullname, '>=', start) & Domain(fullname, '<', end)
                row['__range'] = {group: {'from': start, 'to': end}}
                row[group] = babel.dates.format_date(
                    row[group],
                    format=READ_GROUP_DISPLAY_FORMAT[func],
                    locale=get_lang(self.env).code
                )
        else:
            for row in rows_dict:
                row['__domain'] &= Domain(fullname, '=', row[fullname])