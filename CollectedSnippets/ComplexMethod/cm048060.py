def _compute_date_from_to(self):
        for holiday in self:
            if not holiday.request_date_from:
                holiday.date_from = False
                continue

            if not holiday.request_date_to:
                holiday.date_to = False
                continue

            if holiday.request_unit_hours:
                hour_from = holiday.request_hour_from
                hour_to = holiday.request_hour_to
                if not hour_from or not hour_to:
                    computed_from, computed_to = holiday._get_hour_from_to(holiday.request_date_from, holiday.request_date_to)
                    hour_from = hour_from or computed_from
                    hour_to = hour_to or computed_to

            elif holiday.request_unit_half:
                period_map = {'am': 'morning', 'pm': 'afternoon'}
                from_period = period_map.get(holiday.request_date_from_period)
                to_period = period_map.get(holiday.request_date_to_period)
                if holiday.request_date_from == holiday.request_date_to:
                    day_period = from_period if from_period == to_period else None
                    hour_from, hour_to = holiday._get_hour_from_to(holiday.request_date_from, holiday.request_date_to,
                        day_period)
                else:
                    hour_from, _ = holiday._get_hour_from_to(holiday.request_date_from, holiday.request_date_from, from_period)
                    _, hour_to = holiday._get_hour_from_to(holiday.request_date_to, holiday.request_date_to, to_period)

            else:
                hour_from, hour_to = holiday._get_hour_from_to(holiday.request_date_from, holiday.request_date_to)

            holiday.date_from = self._to_utc(holiday.request_date_from, hour_from, holiday.employee_id or holiday)
            holiday.date_to = self._to_utc(holiday.request_date_to, hour_to, holiday.employee_id or holiday)