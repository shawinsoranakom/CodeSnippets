async def subprocess_exec(self, protocol_factory, program, *args,
                              stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, universal_newlines=False,
                              shell=False, bufsize=0,
                              encoding=None, errors=None, text=None,
                              **kwargs):
        if universal_newlines:
            raise ValueError("universal_newlines must be False")
        if shell:
            raise ValueError("shell must be False")
        if bufsize != 0:
            raise ValueError("bufsize must be 0")
        if text:
            raise ValueError("text must be False")
        if encoding is not None:
            raise ValueError("encoding must be None")
        if errors is not None:
            raise ValueError("errors must be None")

        popen_args = (program,) + args
        protocol = protocol_factory()
        debug_log = None
        if self._debug:
            # don't log parameters: they may contain sensitive information
            # (password) and may be too long
            debug_log = f'execute program {program!r}'
            self._log_subprocess(debug_log, stdin, stdout, stderr)
        transport = await self._make_subprocess_transport(
            protocol, popen_args, False, stdin, stdout, stderr,
            bufsize, **kwargs)
        if self._debug and debug_log is not None:
            logger.info('%s: %r', debug_log, transport)
        return transport, protocol