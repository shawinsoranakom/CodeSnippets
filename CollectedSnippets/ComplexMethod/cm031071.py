def wrap_script(cls, script, *, stdout=True, stderr=False, exc=False):
        script = dedent(script).strip(os.linesep)
        imports = [
            f'import {__name__} as _interp_utils',
        ]
        wrapped = script

        # Handle exc.
        if exc:
            exc = os.pipe()
            r_exc, w_exc = exc
            indented = wrapped.replace('\n', '\n        ')
            wrapped = cls.EXC.format(
                w_pipe=w_exc,
                indented=indented,
            )
        else:
            exc = None

        # Handle stdout.
        if stdout:
            imports.extend([
                'import contextlib, io',
            ])
            stdout = os.pipe()
            r_out, w_out = stdout
            indented = wrapped.replace('\n', '\n        ')
            wrapped = cls.STDIO.format(
                w_pipe=w_out,
                indented=indented,
                stream='out',
            )
        else:
            stdout = None

        # Handle stderr.
        if stderr == 'stdout':
            stderr = None
        elif stderr:
            if not stdout:
                imports.extend([
                    'import contextlib, io',
                ])
            stderr = os.pipe()
            r_err, w_err = stderr
            indented = wrapped.replace('\n', '\n        ')
            wrapped = cls.STDIO.format(
                w_pipe=w_err,
                indented=indented,
                stream='err',
            )
        else:
            stderr = None

        if wrapped == script:
            raise NotImplementedError
        else:
            for line in imports:
                wrapped = f'{line}{os.linesep}{wrapped}'

        results = cls(stdout, stderr, exc)
        return wrapped, results