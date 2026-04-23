def _parse_date_from_data(self, data, index, name, field_type, options):
        dt = datetime.datetime
        fmt = fields.Date.to_string if field_type == 'date' else fields.Datetime.to_string
        d_fmt = options.get('date_format') or DEFAULT_SERVER_DATE_FORMAT
        dt_fmt = options.get('datetime_format') or DEFAULT_SERVER_DATETIME_FORMAT
        for num, line in enumerate(data):
            if not line[index] or isinstance(line[index], datetime.date):
                continue

            v = line[index].strip()
            try:
                # first try parsing as a datetime if it's one
                if dt_fmt and field_type == 'datetime':
                    try:
                        line[index] = fmt(dt.strptime(v, dt_fmt))
                        continue
                    except ValueError:
                        pass
                # otherwise try parsing as a date whether it's a date
                # or datetime
                line[index] = fmt(dt.strptime(v, d_fmt))
            except ValueError as e:
                raise ImportValidationError(
                    _("Column %(column)s contains incorrect values. Error in line %(line)d: %(error)s", column=name, line=num + 1, error=e),
                    field=name, field_type=field_type
                )
            except Exception as e:
                raise ImportValidationError(
                    _("Error Parsing Date [%(field)s:L%(line)d]: %(error)s", field=name, line=num + 1, error=e),
                    field=name, field_type=field_type
                )