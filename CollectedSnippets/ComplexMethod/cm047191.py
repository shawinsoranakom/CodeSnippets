def process_work(self):
        """Process a single database."""
        _logger.debug("WorkerCron (%s) polling for jobs", self.pid)

        if not self.db_queue:
            # list databases
            db_names = OrderedSet(cron_database_list())
            pg_conn = self.dbcursor._cnx
            notified = OrderedSet(
                notif.payload
                for notif in pg_conn.notifies
                if notif.channel == 'cron_trigger'
            )
            pg_conn.notifies.clear()  # free resources
            # add notified databases (in order) first in the queue
            self.db_queue.extend(db for db in notified if db in db_names)
            self.db_queue.extend(db for db in db_names if db not in notified)
            self.db_count = len(self.db_queue)
            if not self.db_count:
                return

        # pop the leftmost element (because notified databases appear first)
        db_name = self.db_queue.popleft()
        self.setproctitle(db_name)

        from odoo.addons.base.models.ir_cron import IrCron  # noqa: PLC0415
        IrCron._process_jobs(db_name)

        # dont keep cursors in multi database mode
        if self.db_count > 1:
            sql_db.close_db(db_name)

        self.request_count += 1
        if self.request_count >= self.request_max and self.request_max < self.db_count:
            _logger.error(
                "There are more dabatases to process than allowed "
                "by the `limit_request` configuration variable: %s more.",
                self.db_count - self.request_max,
            )