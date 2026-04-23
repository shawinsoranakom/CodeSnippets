def _search_work_time_rate(self, operator, value):
        if operator in ('in', 'not in'):
            if not all(isinstance(v, int) for v in value):
                return NotImplemented
        elif operator in ('<', '>'):
            if not isinstance(value, int):
                return NotImplemented
        else:
            return NotImplemented

        calendar_ids = self.env['resource.calendar'].search([])
        if operator == 'in':
            calender = calendar_ids.filtered(lambda m: m.work_time_rate in value)
        elif operator == 'not in':
            calender = calendar_ids.filtered(lambda m: m.work_time_rate not in value)
        elif operator == '<':
            calender = calendar_ids.filtered(lambda m: m.work_time_rate < value)
        elif operator == '>':
            calender = calendar_ids.filtered(lambda m: m.work_time_rate > value)
        return [('id', 'in', calender.ids)]