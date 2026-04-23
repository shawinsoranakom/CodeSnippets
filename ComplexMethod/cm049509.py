def _generate_work_entries(self, date_start, date_stop, force=False):
        # Generate work entries between 2 dates (datetime.datetime)
        # This method considers that the dates are correctly localized
        # based on the target timezone
        assert isinstance(date_start, datetime)
        assert isinstance(date_stop, datetime)
        self = self.with_context(tracking_disable=True)  # noqa: PLW0642
        vals_list = []
        self.write({'last_generation_date': fields.Date.today()})

        intervals_to_generate = defaultdict(lambda: self.env['hr.version'])
        # In case the date_generated_from == date_generated_to, move it to the date_start to
        # avoid trying to generate several months/years of history for old versions for which
        # we've never generated the work entries.
        self.filtered(lambda c: c.date_generated_from == c.date_generated_to).write({
            'date_generated_from': date_start,
            'date_generated_to': date_start,
        })
        domain_to_nullify = Domain(False)
        work_entry_null_vals = {field: False for field in self.env["hr.work.entry.regeneration.wizard"]._work_entry_fields_to_nullify()}

        for tz, versions in self.grouped("tz").items():
            tz = pytz.timezone(tz) if tz else pytz.utc
            for version in versions:
                if not version.contract_date_start:
                    continue

                version_start = tz.localize(fields.Datetime.to_datetime(version.date_start)).astimezone(pytz.utc).replace(tzinfo=None)
                version_stop = tz.localize(datetime.combine(fields.Datetime.to_datetime(version.date_end or date_stop),
                                                 datetime.max.time())).astimezone(pytz.utc).replace(tzinfo=None)
                if version_stop < date_stop:
                    if version.date_generated_from != version.date_generated_to:
                        domain_to_nullify |= Domain([
                            ('version_id', '=', version.id),
                            ('date', '>', version_stop.astimezone(tz)),
                            ('date', '<=', date_stop.astimezone(tz)),
                            ('state', '!=', 'validated'),
                        ])
                if date_start > version_stop or date_stop < version_start:
                    continue
                date_start_work_entries = max(date_start, version_start)
                date_stop_work_entries = min(date_stop, version_stop)
                if force:
                    domain_to_nullify |= Domain([
                        ('version_id', '=', version.id),
                        ('date', '>=', date_start_work_entries.astimezone(tz).date()),
                        ('date', '<=', date_stop_work_entries.astimezone(tz).date()),
                        ('state', '!=', 'validated'),
                    ])
                    intervals_to_generate[date_start_work_entries, date_stop_work_entries] |= version
                    continue

                # For each version, we found each interval we must generate
                # In some cases we do not want to set the generated dates beforehand, since attendance based work entries
                #  is more dynamic, we want to update the dates within the _get_work_entries_values function
                last_generated_from = min(version.date_generated_from, version_stop)
                if last_generated_from > date_start_work_entries:
                    version.date_generated_from = date_start_work_entries
                    intervals_to_generate[date_start_work_entries, last_generated_from] |= version

                last_generated_to = max(version.date_generated_to, version_start)
                if last_generated_to < date_stop_work_entries:
                    version.date_generated_to = date_stop_work_entries
                    intervals_to_generate[last_generated_to, date_stop_work_entries] |= version

        for interval, versions in intervals_to_generate.items():
            date_from, date_to = interval
            vals_list.extend(versions._get_work_entries_values(date_from, date_to))

        if domain_to_nullify != Domain.FALSE:
            work_entries_to_nullify = self.env['hr.work.entry'].search(domain_to_nullify)
            work_entries_to_nullify.write(work_entry_null_vals)

        if not vals_list:
            return self.env['hr.work.entry']

        vals_list = self._generate_work_entries_postprocess(vals_list)
        return self.env['hr.work.entry'].create(vals_list)