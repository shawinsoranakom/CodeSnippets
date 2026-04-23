def _get_profiler_context_manager(self):
        """
        Get a profiler when the profiling is enabled and the requested
        URL is profile-safe. Otherwise, get a context-manager that does
        nothing.
        """
        if self.session.get('profile_session') and self.db:
            if self.session['profile_expiration'] < str(datetime.now()):
                # avoid having session profiling for too long if user forgets to disable profiling
                self.session['profile_session'] = None
                _logger.warning("Profiling expiration reached, disabling profiling")
            elif 'set_profiling' in self.httprequest.path:
                _logger.debug("Profiling disabled on set_profiling route")
            elif self.httprequest.path.startswith('/websocket'):
                _logger.debug("Profiling disabled for websocket")
            elif odoo.evented:
                # only longpolling should be in a evented server, but this is an additional safety
                _logger.debug("Profiling disabled for evented server")
            else:
                try:
                    return profiler.Profiler(
                        db=self.db,
                        description=self.httprequest.full_path,
                        profile_session=self.session['profile_session'],
                        collectors=self.session['profile_collectors'],
                        params=self.session['profile_params'],
                    )._get_cm_proxy()
                except Exception:
                    _logger.exception("Failure during Profiler creation")
                    self.session['profile_session'] = None

        return contextlib.nullcontext()