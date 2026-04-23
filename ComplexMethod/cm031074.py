def interpreter_from_capi(self, config=None, whence=None):
        if config is False:
            if whence is None:
                whence = _interpreters.WHENCE_LEGACY_CAPI
            else:
                assert whence in (_interpreters.WHENCE_LEGACY_CAPI,
                                  _interpreters.WHENCE_UNKNOWN), repr(whence)
            config = None
        elif config is True:
            config = _interpreters.new_config('default')
        elif config is None:
            if whence not in (
                _interpreters.WHENCE_LEGACY_CAPI,
                _interpreters.WHENCE_UNKNOWN,
            ):
                config = _interpreters.new_config('legacy')
        elif isinstance(config, str):
            config = _interpreters.new_config(config)

        if whence is None:
            whence = _interpreters.WHENCE_XI

        interpid = _testinternalcapi.create_interpreter(config, whence=whence)
        try:
            yield interpid
        finally:
            try:
                _testinternalcapi.destroy_interpreter(interpid)
            except _interpreters.InterpreterNotFoundError:
                pass