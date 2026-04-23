def _process_jobs(db_name: str) -> None:
        """ Execute every job ready to be run on this database. """
        try:
            db = sql_db.db_connect(db_name)
            threading.current_thread().dbname = db_name
            with db.cursor() as cron_cr:
                cls = IrCron
                cls._check_version(cron_cr)
                jobs = cls._get_all_ready_jobs(cron_cr)
                if not jobs:
                    return
                cls._check_modules_state(cron_cr, jobs)
                cls._process_jobs_loop(cron_cr, job_ids=[job['id'] for job in jobs])
        except BadVersion:
            _logger.warning('Skipping database %s as its base version is not %s.', db_name, BASE_VERSION)
        except BadModuleState:
            _logger.warning('Skipping database %s because of modules to install/upgrade/remove.', db_name)
        except psycopg2.errors.UndefinedTable:
            # The table ir_cron does not exist; this is probably not an OpenERP database.
            _logger.warning('Tried to poll an undefined table on database %s.', db_name)
        except psycopg2.ProgrammingError:
            raise
        except Exception:
            _logger.warning('Exception in cron:', exc_info=True)
        finally:
            if hasattr(threading.current_thread(), 'dbname'):
                del threading.current_thread().dbname