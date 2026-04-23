def _compute_calendar_display_name(self):
        companies = self.company_id
        encoding_in_days_per_company = dict(zip(companies, [company.timesheet_encode_uom_id == self.env.ref('uom.product_uom_day') for company in companies]))
        for line in self:
            if not line.project_id:
                line.calendar_display_name = ""
                continue
            if encoding_in_days_per_company[line.company_id]:
                days = line._get_timesheet_time_day()
                if days == int(days):
                    days = int(days)
                line.calendar_display_name = self.env._(
                    "%(project_name)s (%(days)sd)",
                    project_name=line.project_id.display_name,
                    days=days,
                )
            else:
                minutes = round(line.unit_amount * 60)
                hours, minutes = divmod(abs(round(minutes)), 60)
                if minutes:
                    line.calendar_display_name = self.env._(
                        "%(project_name)s (%(sign)s%(hours)sh%(minutes)s)",
                        project_name=line.project_id.display_name,
                        sign='-' if line.unit_amount < 0 else '',
                        hours=hours,
                        minutes=minutes,
                    )
                else:
                    line.calendar_display_name = self.env._(
                        "%(project_name)s (%(sign)s%(hours)sh)",
                        project_name=line.project_id.display_name,
                        sign='-' if line.unit_amount < 0 else '',
                        hours=hours,
                    )