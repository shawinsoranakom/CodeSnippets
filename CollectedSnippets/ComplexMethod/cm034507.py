def _valid_time_stamp(self, timestamp_str):
        """ Return a valid time object from the given time string """
        DT_RE = re.compile(r'^(\d{4})(\d{2})(\d{2})\.(\d{2})(\d{2})(\d{2})$')
        match = DT_RE.match(timestamp_str)
        epoch_date_time = (1980, 1, 1, 0, 0, 0, 0, 0, -1)
        if match:
            try:
                if int(match.groups()[0]) < 1980:
                    date_time = epoch_date_time
                elif int(match.groups()[0]) >= 2038 and _y2038_impacted():
                    date_time = (2038, 1, 1, 0, 0, 0, 0, 0, -1)
                elif int(match.groups()[0]) > 2107:
                    date_time = (2107, 12, 31, 23, 59, 59, 0, 0, -1)
                else:
                    date_time = (int(m) for m in match.groups() + (0, 0, -1))
            except ValueError:
                date_time = epoch_date_time
        else:
            # Assume epoch date
            date_time = epoch_date_time

        return time.mktime(time.struct_time(date_time))