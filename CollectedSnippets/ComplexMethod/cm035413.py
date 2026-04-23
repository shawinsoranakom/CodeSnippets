def filter(self, record: logging.LogRecord) -> bool:
        from openhands.utils._redact_compat import redact_url_params

        if record.args:
            if isinstance(record.args, (tuple, list)):
                record.args = tuple(
                    redact_url_params(arg)
                    if isinstance(arg, str) and '?' in arg
                    else arg
                    for arg in record.args
                )
            elif isinstance(record.args, dict):
                record.args = {
                    k: redact_url_params(v) if isinstance(v, str) and '?' in v else v
                    for k, v in record.args.items()
                }

        if '?' in record.msg:
            record.msg = self._URL_WITH_QS_RE.sub(
                lambda m: redact_url_params(m.group(0)), record.msg
            )

        return True