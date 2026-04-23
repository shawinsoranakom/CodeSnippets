def _clean_js_runtimes(self, runtimes):
        if not (
            isinstance(runtimes, dict)
            and all(isinstance(k, str) and (v is None or isinstance(v, dict)) for k, v in runtimes.items())
        ):
            raise ValueError('Invalid js_runtimes format, expected a dict of {runtime: {config}}')

        if unsupported_runtimes := runtimes.keys() - supported_js_runtimes.value.keys():
            self.report_warning(
                f'Ignoring unsupported JavaScript runtime(s): {", ".join(unsupported_runtimes)}.'
                f' Supported runtimes: {", ".join(supported_js_runtimes.value.keys())}.')
            for rt in unsupported_runtimes:
                runtimes.pop(rt)