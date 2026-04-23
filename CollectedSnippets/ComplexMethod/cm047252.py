def _run_vacuum_cleaner(self):
        """
        Perform a complete database cleanup by safely calling every
        ``@api.autovacuum`` decorated method.
        """
        if not self.env.is_admin() or not self.env.context.get('cron_id'):
            raise AccessDenied()

        all_methods = [
            (model, attr, func)
            for model in self.env.values()
            for attr, func in inspect.getmembers(model.__class__, is_autovacuum)
        ]
        # shuffle methods at each run, prevents one blocking method from always
        # starving the following ones
        random.shuffle(all_methods)
        queue = collections.deque(all_methods)
        while queue and self.env['ir.cron']._commit_progress(remaining=len(queue)):
            model, attr, func = queue.pop()
            _logger.debug('Calling %s.%s()', model, attr)
            try:
                start_time = time.monotonic()
                result = func(model)
                self.env['ir.cron']._commit_progress(1)
                if isinstance(result, tuple) and len(result) == 2:
                    func_done, func_remaining = result
                    _logger.debug(
                        '%s.%s  vacuumed %r records, remaining %r',
                        model, attr, func_done, func_remaining,
                    )
                    if func_remaining:
                        queue.appendleft((model, attr, func))
                _logger.debug("%s.%s  took %.2fs", model, attr, time.monotonic() - start_time)
            except Exception:
                _logger.exception("Failed %s.%s()", model, attr)
                self.env.cr.rollback()