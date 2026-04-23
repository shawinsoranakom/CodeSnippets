def _run_cron(cr):
            pg_conn = cr._cnx
            # LISTEN / NOTIFY doesn't work in recovery mode
            cr.execute("SELECT pg_is_in_recovery()")
            in_recovery = cr.fetchone()[0]
            if not in_recovery:
                cr.execute("LISTEN cron_trigger")
            else:
                _logger.warning("PG cluster in recovery mode, cron trigger not activated")
            cr.commit()
            check_all_time = 0.0  # last time that we listed databases, initialized far in the past
            all_db_names = []
            alive_time = time.monotonic()
            while config['limit_time_worker_cron'] <= 0 or (time.monotonic() - alive_time) <= config['limit_time_worker_cron']:
                select.select([pg_conn], [], [], SLEEP_INTERVAL + number)
                time.sleep(number / 100)
                try:
                    pg_conn.poll()
                except Exception:
                    if pg_conn.closed:
                        # connection closed, just exit the loop
                        return
                    raise
                notified = OrderedSet(
                    notif.payload
                    for notif in pg_conn.notifies
                    if notif.channel == 'cron_trigger'
                )
                pg_conn.notifies.clear()  # free resources

                if time.time() - SLEEP_INTERVAL > check_all_time:
                    # check all databases
                    # last time we checked them was `now - SLEEP_INTERVAL`
                    check_all_time = time.time()
                    # process notified databases first, then the other ones
                    all_db_names = OrderedSet(cron_database_list())
                    db_names = [
                        *(db for db in notified if db in all_db_names),
                        *(db for db in all_db_names if db not in notified),
                    ]
                else:
                    # restrict to notified databases only
                    db_names = notified.intersection(all_db_names)
                    if not db_names:
                        continue

                _logger.debug('cron%d polling for jobs (notified: %s)', number, notified)
                for db_name in db_names:
                    thread = threading.current_thread()
                    thread.start_time = time.time()
                    try:
                        IrCron._process_jobs(db_name)
                    except Exception:
                        _logger.warning('cron%d encountered an Exception:', number, exc_info=True)
                    thread.start_time = None