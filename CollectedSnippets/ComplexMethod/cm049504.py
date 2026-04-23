def regenerate_work_entries(self, slots=None, record_ids=None):
        if not slots:
            if not self.env.context.get('work_entry_skip_validation'):
                if not self.search_criteria_completed:
                    raise ValidationError(_("In order to regenerate the work entries, you need to provide the wizard with an employee_id, a date_from and a date_to."))

                if self.date_from < self.earliest_available_date or self.date_to > self.latest_available_date:
                    raise ValidationError(_("The from date must be >= '%(earliest_available_date)s' and the to date must be <= '%(latest_available_date)s', which correspond to the generated work entries time interval.", earliest_available_date=self._date_to_string(self.earliest_available_date), latest_available_date=self._date_to_string(self.latest_available_date)))

                if not self.valid:
                    raise ValidationError(self.env._("No work entry can be regenerated in this range of dates and these employees."))

            valid_employees = self.employee_ids - self.validated_work_entry_employee_ids
            date_from = max(self.date_from, self.earliest_available_date) if self.earliest_available_date else self.date_from
            date_to = min(self.date_to, self.latest_available_date) if self.latest_available_date else self.date_to
            valid_employees.generate_work_entries(date_from, date_to, True)
        else:
            range_by_employee = defaultdict(list)
            slots.sort(key=lambda d: (d['employee_id'], d['date']))
            for employee_id, records in groupby(slots, lambda d: d['employee_id']):
                dates = [fields.Date.from_string(r['date']) for r in records]
                start = end = dates[0]
                for current in dates[1:]:
                    if current - end != timedelta(days=1):
                        range_by_employee[start, end].append(employee_id)
                        start = current
                    end = current
                range_by_employee[start, end].append(employee_id)
            for (date_from, date_to), employee_ids in range_by_employee.items():
                valid_employees = self.env["hr.employee"].browse(employee_ids)
                valid_employees.generate_work_entries(date_from, date_to, True)