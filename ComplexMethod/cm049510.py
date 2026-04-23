def _generate_work_entries_postprocess(self, vals_list):
        # Convert date_start/date_stop to date/duration
        # Split work entries over 2 days due to timezone conversion
        # Regroup work entries of the same type
        mapped_periods = defaultdict(lambda: defaultdict(lambda: self.env['hr.employee']))
        cached_periods = defaultdict(float)
        tz_by_version = {}

        def _get_tz(version_id):
            if version_id in tz_by_version:
                return tz_by_version[version_id]
            version = self.env['hr.version'].browse(version_id)
            tz = version.resource_calendar_id.tz or version.employee_id.resource_calendar_id.tz or version.company_id.resource_calendar_id.tz
            if not tz:
                raise UserError(_('Missing timezone for work entries generation.'))
            tz = pytz.timezone(tz)
            tz_by_version[version_id] = tz
            return tz

        new_vals_list = []
        for vals in vals_list:
            new_vals = vals.copy()
            if not new_vals.get('date_start') or not new_vals.get('date_stop'):
                new_vals.pop('date_start', False)
                new_vals.pop('date_stop', False)
                if 'duration' not in new_vals or 'date' not in new_vals:
                    raise UserError(_('Missing date or duration on work entry'))
                new_vals_list.append(new_vals)
                continue

            date_start_utc = new_vals['date_start'] if new_vals['date_start'].tzinfo else pytz.UTC.localize(new_vals['date_start'])
            date_stop_utc = new_vals['date_stop'] if new_vals['date_stop'].tzinfo else pytz.UTC.localize(new_vals['date_stop'])

            tz = _get_tz(new_vals['version_id'])
            local_start = date_start_utc.astimezone(tz)
            local_stop = date_stop_utc.astimezone(tz)

            # Handle multi-local-day spans
            current = local_start + timedelta(microseconds=1) if local_start.time() == datetime.max.time() else local_start
            while current < local_stop:
                next_local_midnight = tz.localize(datetime.combine(current.date() + timedelta(days=1), time.min) - timedelta(microseconds=1))
                segment_end = min(local_stop, next_local_midnight)

                partial_vals = new_vals.copy()

                # Convert partial segment back to UTC for consistency
                partial_vals['date_start'] = current.astimezone(pytz.UTC)
                partial_vals['date_stop'] = segment_end.astimezone(pytz.UTC)

                new_vals_list.append(partial_vals)

                current = segment_end + timedelta(microseconds=1)

        vals_list = new_vals_list

        for vals in vals_list:
            if not vals.get('date_start') or not vals.get('date_stop'):
                continue
            date_start = vals['date_start']
            date_stop = vals['date_stop']
            tz = _get_tz(vals['version_id'])
            if not self._generate_work_entries_postprocess_adapt_to_calendar(vals):
                vals['date'] = date_start.astimezone(tz).date()
                if 'duration' in vals:
                    continue
                elif (date_start, date_stop) in cached_periods:
                    vals['duration'] = cached_periods[date_start, date_stop]
                else:
                    dt = date_stop - date_start
                    duration = round(dt.total_seconds()) / 3600  # Number of hours
                    cached_periods[date_start, date_stop] = duration
                    vals['duration'] = duration
                continue
            version = self.env['hr.version'].browse(vals['version_id'])
            calendar = version.resource_calendar_id
            if not calendar:
                vals['date'] = date_start.astimezone(tz).date()
                vals['duration'] = 0.0
                continue
            employee = version.employee_id
            mapped_periods[date_start, date_stop][calendar] |= employee

        # {(date_start, date_stop): {calendar: {'hours': foo}}}
        mapped_version_data = defaultdict(lambda: defaultdict(lambda: {'hours': 0.0}))
        for (date_start, date_stop), employees_by_calendar in mapped_periods.items():
            for calendar, employees in employees_by_calendar.items():
                mapped_version_data[date_start, date_stop][calendar] = employees._get_work_days_data_batch(
                    date_start, date_stop, compute_leaves=False, calendar=calendar)

        for vals in vals_list:
            if 'duration' not in vals:
                date_start = vals['date_start']
                date_stop = vals['date_stop']
                version = self.env['hr.version'].browse(vals['version_id'])
                calendar = version.resource_calendar_id
                employee = version.employee_id
                tz = _get_tz(vals['version_id'])
                vals['date'] = date_start.astimezone(tz).date()
                vals['duration'] = mapped_version_data[date_start, date_stop][calendar][employee.id]['hours'] if calendar else 0.0
            vals.pop('date_start', False)
            vals.pop('date_stop', False)

        # Now merge similar work entries on the same day
        merged_vals = {}
        for vals in vals_list:
            if float_is_zero(vals['duration'], 3):
                continue
            key = (
                vals['date'],
                vals.get('work_entry_type_id', False),
                vals['employee_id'],
                vals['version_id'],
                vals.get('company_id', False),
            )
            if key in merged_vals:
                merged_vals[key]['duration'] += vals.get('duration', 0.0)
            else:
                merged_vals[key] = vals.copy()
        return list(merged_vals.values())