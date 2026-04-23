def traceback_cm():
            restore = loggingutil.hide_emit_errors()
            try:
                yield
            except BrokenPipeError:
                # It was piped to "head" or something similar.
                pass
            except NotImplementedError:
                raise  # re-raise
            except Exception as exc:
                if not showtb:
                    sys.exit(f'ERROR: {exc}')
                raise  # re-raise
            except KeyboardInterrupt:
                if not showtb:
                    sys.exit('\nINTERRUPTED')
                raise  # re-raise
            except BaseException as exc:
                if not showtb:
                    sys.exit(f'{type(exc).__name__}: {exc}')
                raise  # re-raise
            finally:
                restore()