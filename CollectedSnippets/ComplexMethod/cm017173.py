def callproc(self, procname, params=None, kparams=None):
        # Keyword parameters for callproc aren't supported in PEP 249, but the
        # database driver may support them (e.g. oracledb).
        if kparams is not None and not self.db.features.supports_callproc_kwargs:
            raise NotSupportedError(
                "Keyword parameters for callproc are not supported on this "
                "database backend."
            )
        # Raise a warning during app initialization (stored_app_configs is only
        # ever set during testing).
        if not apps.ready and not apps.stored_app_configs:
            warnings.warn(self.APPS_NOT_READY_WARNING_MSG, category=RuntimeWarning)
        self.db.validate_no_broken_transaction()
        with self.db.wrap_database_errors:
            if params is None and kparams is None:
                return self.cursor.callproc(procname)
            elif kparams is None:
                return self.cursor.callproc(procname, params)
            else:
                params = params or ()
                return self.cursor.callproc(procname, params, kparams)