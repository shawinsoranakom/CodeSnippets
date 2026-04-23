def _get_work_entries_values(self, date_start, date_stop):
        """
        Generate a work_entries list between date_start and date_stop for one version.
        :return: list of dictionnary.
        """
        if isinstance(date_start, datetime):
            version_vals = self._get_version_work_entries_values(date_start, date_stop)
        else:
            version_vals = []
            versions_by_tz = defaultdict(lambda: self.env['hr.version'])
            for version in self:
                versions_by_tz[version.resource_calendar_id.tz] += version
            for version_tz, versions in versions_by_tz.items():
                tz = pytz.timezone(version_tz) if version_tz else pytz.utc
                version_vals += versions._get_version_work_entries_values(
                    tz.localize(date_start),
                    tz.localize(date_stop))

        # {version_id: ([dates_start], [dates_stop])}
        mapped_version_dates = defaultdict(lambda: ([], []))
        for x in version_vals:
            mapped_version_dates[x['version_id']][0].append(x['date_start'])
            mapped_version_dates[x['version_id']][1].append(x['date_stop'])

        for version in self:
            # If we generate work_entries which exceeds date_start or date_stop, we change boundaries on version
            if version_vals:
                # Handle empty work entries for certain versions, could happen on an attendance based version
                # NOTE: this does not handle date_stop or date_start not being present in vals
                dates_stop = mapped_version_dates[version.id][1]
                if dates_stop:
                    date_stop_max = max(dates_stop)
                    if date_stop_max > version.date_generated_to:
                        version.date_generated_to = date_stop_max

                dates_start = mapped_version_dates[version.id][0]
                if dates_start:
                    date_start_min = min(dates_start)
                    if date_start_min < version.date_generated_from:
                        version.date_generated_from = date_start_min

        return version_vals