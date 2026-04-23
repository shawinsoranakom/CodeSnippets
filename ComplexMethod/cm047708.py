def end(self):
        if self.done:
            return
        self.done = True
        try:
            for collector in self.collectors:
                collector.stop()
            self.duration = real_time() - self.start_time
            self.cpu_duration = real_cpu_time() - self.start_cpu_time
            self._add_file_lines(self.init_stack_trace)

            if self.db:
                # pylint: disable=import-outside-toplevel
                from odoo.sql_db import db_connect  # only import from odoo if/when needed.
                with db_connect(self.db).cursor() as cr:
                    values = {
                        "name": self.description,
                        "session": self.profile_session,
                        "create_date": real_datetime_now(),
                        "init_stack_trace": json.dumps(_format_stack(self.init_stack_trace)),
                        "duration": self.duration,
                        "cpu_duration": self.cpu_duration,
                        "entry_count": self.entry_count(),
                        "sql_count": sum(len(collector.entries) for collector in self.collectors if collector.name == 'sql')
                    }
                    others = {}
                    for collector in self.collectors:
                        if collector.entries:
                            if collector._store == "others":
                                others[collector.name] = json.dumps(collector.entries)
                            else:
                                values[collector.name] = json.dumps(collector.entries)
                    if others:
                        values['others'] = json.dumps(others)
                    query = SQL(
                        "INSERT INTO ir_profile(%s) VALUES %s RETURNING id",
                        SQL(",").join(map(SQL.identifier, values)),
                        tuple(values.values()),
                    )
                    cr.execute(query)
                    self.profile_id = cr.fetchone()[0]
                    _logger.info('ir_profile %s (%s) created', self.profile_id, self.profile_session)
        except OperationalError:
            _logger.exception("Could not save profile in database")
        finally:
            self.exit_stack.close()
            if self.params:
                del self.init_thread.profiler_params
            if self.log:
                _logger.info(self.summary())