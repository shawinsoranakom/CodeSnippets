def _cron_process_time_based_actions(self):
        """ Execute the time-based automations. """
        if '__action_done' not in self.env.context:
            self = self.with_context(__action_done={})

        # retrieve all the automation rules to run based on a timed condition
        final_exception = None
        automations = self.with_context(active_test=True).search([('trigger', 'in', TIME_TRIGGERS)])
        self.env['ir.cron']._commit_progress(remaining=len(automations))

        for automation in automations:
            # is automation deactivated or disappeared between commits?
            try:
                if not automation.active:
                    continue
            except MissingError:
                continue
            _logger.info("Starting time-based automation rule `%s`.", automation.name)
            now = self.env.cr.now()
            records = automation._search_time_based_automation_records(until=now)
            # run the automation on the records
            try:
                for record in records:
                    automation._process(record)
                self.env.flush_all()
            except Exception as e:
                self.env.cr.rollback()
                _logger.exception("Error in time-based automation rule `%s`.", automation.name)
                final_exception = e
                continue

            automation.write({'last_run': now})
            _logger.info("Time-based automation rule `%s` done.", automation.name)
            if not self.env['ir.cron']._commit_progress(1):
                break
        if final_exception is not None:
            # raise the last found exception to mark the cron job as failing
            raise final_exception