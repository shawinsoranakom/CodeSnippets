def execute_sql(self, sql, params=None, commit=True):
        for attempt in range(self.max_retries + 1):
            try:
                return super().execute_sql(sql, params, commit)
            except (OperationalError, InterfaceError) as e:
                error_codes = [2013, 2006]
                error_messages = ['', 'Lost connection']
                should_retry = (
                    (hasattr(e, 'args') and e.args and e.args[0] in error_codes) or
                    (str(e) in error_messages) or
                    (hasattr(e, '__class__') and e.__class__.__name__ == 'InterfaceError')
                )

                if should_retry and attempt < self.max_retries:
                    logging.warning(
                        f"Database connection issue (attempt {attempt+1}/{self.max_retries}): {e}"
                    )
                    self._handle_connection_loss()
                    time.sleep(self.retry_delay * (2 ** attempt))
                else:
                    logging.error(f"DB execution failure: {e}")
                    raise
        return None