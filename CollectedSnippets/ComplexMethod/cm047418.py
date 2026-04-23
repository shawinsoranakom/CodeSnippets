def _trigger_list(self, at_list: list[datetime]):
        """
        Implementation of :meth:`~._trigger`.

        :param at_list: Execute the cron later, at precise moments in time.
        :return: the created triggers records
        """
        self.ensure_one()
        now = fields.Datetime.now()

        if not self.sudo().active:
            # skip triggers that would be ignored
            at_list = [at for at in at_list if at > now]

        if not at_list:
            return self.env['ir.cron.trigger']

        triggers = self.env['ir.cron.trigger'].sudo().create([
            {'cron_id': self.id, 'call_at': at}
            for at in at_list
        ])
        if _logger.isEnabledFor(logging.DEBUG):
            ats = ', '.join(map(str, at_list))
            _logger.debug('Job %r (%s) will execute at %s', self.sudo().name, self.id, ats)

        if min(at_list) <= now or os.getenv('ODOO_NOTIFY_CRON_CHANGES'):
            self.env.cr.postcommit.add(self._notifydb)
        return triggers