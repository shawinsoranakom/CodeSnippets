def __init__(self, args, *remaining, env=None, text=False, shell=False, **kwargs):
        if env is None:
            env = os.environ.copy()
        self._fix_pyinstaller_issues(env)

        self.__text_mode = kwargs.get('encoding') or kwargs.get('errors') or text or kwargs.get('universal_newlines')
        if text is True:
            kwargs['universal_newlines'] = True  # For 3.6 compatibility
            kwargs.setdefault('encoding', 'utf-8')
            kwargs.setdefault('errors', 'replace')

        if os.name == 'nt' and kwargs.get('executable') is None:
            # Must apply shell escaping if we are trying to run a batch file
            # These conditions should be very specific to limit impact
            if not shell and isinstance(args, list) and args and args[0].lower().endswith(('.bat', '.cmd')):
                shell = True

            if shell:
                if not isinstance(args, str):
                    args = shell_quote(args, shell=True)
                shell = False
                # Set variable for `cmd.exe` newline escaping (see `utils.shell_quote`)
                env['='] = '"^\n\n"'
                args = f'{self.__comspec()} /Q /S /D /V:OFF /E:ON /C "{args}"'

        super().__init__(args, *remaining, env=env, shell=shell, **kwargs, startupinfo=self._startupinfo)