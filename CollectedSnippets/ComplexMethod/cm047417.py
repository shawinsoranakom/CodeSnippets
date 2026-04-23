def _run_job(cls, job) -> CompletionStatus:
        """
        Execute the job's server action multiple times until it
        completes. The completion status is returned.

        It is considered completed when either:

        - the server action doesn't use the progress API, or returned
          and notified that all records has been processed: ``'fully done'``;

        - the server action returned and notified that there are
          remaining records to process, but this cron worker ran this
          server action 10 times already: ``'partially done'``;

        - the server action was able to commit and notify some work done,
          but later crashed due to an exception: ``'partially done'``;

        - the server action failed due to an exception and no progress
          was notified: ``'failed'``.
        """
        timed_out_counter = job['timed_out_counter']

        with cls.pool.cursor() as job_cr:
            start_time = time.monotonic()
            env = api.Environment(job_cr, job['user_id'], {
                'lastcall': job['lastcall'],
                'cron_id': job['id'],
                'cron_end_time': start_time + MIN_TIME_PER_JOB,
            })
            cron = env[cls._name].browse(job['id'])

            status = None
            loop_count = 0
            _logger.info('Job %r (%s) starting', job['cron_name'], job['id'])

            # stop after MIN_RUNS_PER_JOB runs and MIN_TIME_PER_JOB seconds, or
            # upon full completion or failure
            while status is None and (
                loop_count < MIN_RUNS_PER_JOB
                or time.monotonic() < env.context['cron_end_time']
            ):
                cron, progress = cron._add_progress(timed_out_counter=timed_out_counter)
                job_cr.commit()

                success = False
                try:
                    # signaling check and commit is done inside `_callback`
                    cron._callback(job['cron_name'], job['ir_actions_server_id'])
                    success = True
                except Exception:  # noqa: BLE001
                    _logger.exception('Job %r (%s) server action #%s failed',
                        job['cron_name'], job['id'], job['ir_actions_server_id'])
                finally:
                    done, remaining = progress.done, progress.remaining
                    match (success, done, remaining):
                        case (False, d, r) if d and r:
                            # The cron action failed but was nonetheless able
                            # to commit some progress.
                            # Hopefully this failure is temporary.
                            pass

                        case (False, _, _):
                            # The cron action failed, and was unable to commit
                            # any progress this time. Consider it failed even
                            # if it progressed in a previous loop iteration.
                            status = CompletionStatus.FAILED

                        case (True, _, 0):
                            # The cron action completed. Either it doesn't use
                            # the progress API, either it reported no remaining
                            # stuff to process.
                            status = CompletionStatus.FULLY_DONE
                            if progress.deactivate:
                                job['active'] = False

                        case (True, 0, _) if loop_count == 0:
                            # The cron action was able to determine there are
                            # remaining records to process, but couldn't
                            # process any of them.
                            # Hopefully this condition is temporary.
                            status = CompletionStatus.PARTIALLY_DONE
                            _logger.warning("Job %r (%s) processed no record",
                                job['cron_name'], job['id'])

                        case (True, 0, _):
                            # The cron action was able to determine there are
                            # remaining records to process, did process some
                            # records in a previous loop iteration, but
                            # processed none this time.
                            status = CompletionStatus.PARTIALLY_DONE

                        case (True, _, _):
                            # The cron action was able to process some but not
                            # all records. Loop.
                            pass

                    loop_count += 1
                    progress.timed_out_counter = 0
                    timed_out_counter = 0
                    job_cr.commit()  # ensure we have no leftovers

                    _logger.debug('Job %r (%s) processed %s records, %s records remaining',
                        job['cron_name'], job['id'], done, remaining)

            status = status or CompletionStatus.PARTIALLY_DONE
            _logger.info(
                'Job %r (%s) %s (#loop %s; done %s; remaining %s; duration %.2fs)',
                job['cron_name'], job['id'], status,
                loop_count, done, remaining, time.monotonic() - start_time)

        return status