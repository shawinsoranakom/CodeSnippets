def _search_time_based_automation_records(self, *, until):
        automation = self.ensure_one()

        # retrieve the domain and field
        domain = Domain.TRUE
        if automation.filter_domain:
            eval_context = automation._get_eval_context()
            domain = Domain(safe_eval.safe_eval(automation.filter_domain, eval_context))
        Model = self.env[automation.model_name]
        date_field = Model._fields.get(automation.trg_date_id.name)
        if not date_field:
            _logger.warning("Missing date trigger field in automation rule `%s`", automation.name)
            return Model

        # get the time information and find the records
        last_run = automation.last_run or datetime.datetime.fromtimestamp(0, tz=None)
        is_date_automation_last = date_field.name == "date_automation_last" and "create_date" in Model._fields
        range_sign = 1 if automation.trg_date_range_mode == 'before' else -1
        date_range = range_sign * automation.trg_date_range

        def get_record_dt(record):
            # the field can be a date or datetime, cast always to a datetime
            dt = record[date_field.name]
            if not dt and is_date_automation_last:
                dt = record.create_date
            return fields.Datetime.to_datetime(dt)

        if automation.trg_date_calendar_id and automation.trg_date_range_type == 'day':
            # use the calendar information from the record
            # _get_calendar can be overwritten and cannot be optimized
            time_domain = Domain.TRUE if is_date_automation_last else Domain(date_field.name, '!=', False)
            if (date_field.store or date_field.search):
                records = Model.search(time_domain & domain)
            else:
                records = Model.search(domain).filtered_domain(time_domain)

            past_until = {}
            past_last_run = {}

            def calendar_filter(record):
                record_dt = get_record_dt(record)
                if not record_dt:
                    return False
                calendar = self._get_calendar(automation, record)
                if calendar.id not in past_until:
                    past_until[calendar.id] = calendar.plan_days(
                        date_range,
                        until,
                        compute_leaves=True,
                    )
                    past_last_run[calendar.id] = calendar.plan_days(
                        date_range,
                        last_run,
                        compute_leaves=True,
                    )
                return past_last_run[calendar.id] <= record_dt < past_until[calendar.id]

            return records.filtered(calendar_filter)

        # we can search for the records to trigger
        # find the relative dates
        relative_offset = DATE_RANGE[automation.trg_date_range_type] * date_range
        relative_until = until + relative_offset
        relative_last_run = last_run + relative_offset
        if date_field.type == 'date':
            # find records that have a date in past, but were not yet executed that day
            time_domain = Domain(date_field.name, '>', relative_last_run.date()) & Domain(date_field.name, '<=', relative_until.date())
            if is_date_automation_last:
                time_domain |= Domain(date_field.name, '=', False) & Domain('create_date', '>', relative_last_run.date()) & Domain('create_date', '<=', relative_until.today())
        else:  # datetime
            time_domain = Domain(date_field.name, '>=', relative_last_run) & Domain(date_field.name, '<', relative_until)
            if is_date_automation_last:
                time_domain |= Domain(date_field.name, '=', False) & Domain('create_date', '>=', relative_last_run) & Domain('create_date', '<', relative_until)

        if (date_field.store or date_field.search):
            return Model.search(time_domain & domain)
        else:
            return Model.search(domain).filtered_domain(time_domain)