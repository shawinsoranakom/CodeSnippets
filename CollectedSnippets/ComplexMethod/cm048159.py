def get_timesheets():
            field = None if groupby == 'none' else groupby
            orderby = '%s, %s' % (field, sortby) if field else sortby
            timesheets = Timesheet_sudo.search(domain, order=orderby, limit=items_per_page, offset=pager['offset'])
            if field:
                if groupby == 'date':
                    raw_timesheets_group = Timesheet_sudo._read_group(
                        domain, ['date:day'], ['unit_amount:sum', 'id:recordset'], order='date:day desc'
                    )
                    grouped_timesheets = [(records, unit_amount) for __, unit_amount, records in raw_timesheets_group]

                else:
                    time_data = Timesheet_sudo._read_group(domain, [field], ['unit_amount:sum'])
                    mapped_time = {field.id: unit_amount for field, unit_amount in time_data}
                    grouped_timesheets = [(Timesheet_sudo.concat(*g), mapped_time[k.id]) for k, g in groupbyelem(timesheets, itemgetter(field))]
                return timesheets, grouped_timesheets

            grouped_timesheets = [(
                timesheets,
                Timesheet_sudo._read_group(domain, aggregates=['unit_amount:sum'])[0][0]
            )] if timesheets else []
            return timesheets, grouped_timesheets