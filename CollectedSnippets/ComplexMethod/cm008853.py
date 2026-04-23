def report_retry(e, count, retries, *, sleep_func, info, warn, error=None, suffix=None):
        """Utility function for reporting retries"""
        if count > retries:
            if error:
                return error(f'{e}. Giving up after {count - 1} retries') if count > 1 else error(str(e))
            raise e

        if not count:
            return warn(e)
        elif isinstance(e, ExtractorError):
            e = remove_end(str_or_none(e.cause) or e.orig_msg, '.')
        warn(f'{e}. Retrying{format_field(suffix, None, " %s")} ({count}/{retries})...')

        delay = float_or_none(sleep_func(n=count - 1)) if callable(sleep_func) else sleep_func
        if delay:
            info(f'Sleeping {delay:.2f} seconds ...')
            time.sleep(delay)