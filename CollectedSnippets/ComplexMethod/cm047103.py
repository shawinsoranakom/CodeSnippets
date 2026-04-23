def emit(self, record):
        ct = threading.current_thread()
        ct_db = getattr(ct, 'dbname', None)
        dbname = tools.config['log_db'] if tools.config['log_db'] and tools.config['log_db'] != '%d' else ct_db
        if not dbname:
            return
        with contextlib.suppress(Exception), tools.mute_logger('odoo.sql_db'), sql_db.db_connect(dbname, allow_uri=True).cursor() as cr:
            # preclude risks of deadlocks
            cr.execute("SET LOCAL statement_timeout = 1000")
            msg = str(record.msg)
            if record.args:
                msg = msg % record.args
            traceback = getattr(record, 'exc_text', '')
            if traceback:
                msg = f"{msg}\n{traceback}"
            # we do not use record.levelname because it may have been changed by ColoredFormatter.
            levelname = logging.getLevelName(record.levelno)

            val = ('server', ct_db, record.name, levelname, msg, record.pathname, record.lineno, record.funcName)

            if self._support_metadata:
                from . import modules
                metadata = {}
                if modules.module.current_test:
                    with contextlib.suppress(Exception):
                        metadata['test'] = modules.module.current_test.get_log_metadata()

                if metadata:
                    cr.execute("""
                        INSERT INTO ir_logging(create_date, type, dbname, name, level, message, path, line, func, metadata)
                        VALUES (NOW() at time zone 'UTC', %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (*val, json.dumps(metadata)))
                    return

            cr.execute("""
                INSERT INTO ir_logging(create_date, type, dbname, name, level, message, path, line, func)
                VALUES (NOW() at time zone 'UTC', %s, %s, %s, %s, %s, %s, %s, %s)
            """, val)