def _compute_date_finished(self):
        for production in self:
            if not production.date_start or production.is_planned or production.state == 'done':
                continue
            days_delay = production.bom_id.produce_delay
            date_finished = production.date_start + relativedelta(days=days_delay)
            if production._should_postpone_date_finished(date_finished):
                date_finished = production._calculate_expected_finished_date(date_finished) or \
                    (date_finished + relativedelta(minutes=sum(production.workorder_ids.mapped('duration_expected')) or 60))
            production.date_finished = date_finished