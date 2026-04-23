def _compute_maintenance_request(self):
        for record in self:
            maintenance_requests = record.maintenance_ids.filtered(lambda mr: mr.maintenance_type == 'corrective' and mr.stage_id.done)
            record.mttr = len(maintenance_requests) and (sum(int((request.close_date - request.request_date).days) if request.close_date and request.request_date else 0 for request in maintenance_requests) / len(maintenance_requests)) or 0
            record.latest_failure_date = max((request.request_date for request in maintenance_requests), default=False)
            record.mtbf = record.latest_failure_date and (record.latest_failure_date - record.effective_date).days / len(maintenance_requests) or 0
            record.estimated_next_failure = record.mtbf and record.latest_failure_date + relativedelta(days=record.mtbf) or False