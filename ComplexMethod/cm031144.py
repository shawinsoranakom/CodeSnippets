def ensure_directories(self, env_dir):
        """
        Create the directories for the environment.

        Returns a context object which holds paths in the environment,
        for use by subsequent logic.
        """

        def create_if_needed(d):
            if not os.path.exists(d):
                os.makedirs(d)
            elif os.path.islink(d) or os.path.isfile(d):
                raise ValueError('Unable to create directory %r' % d)

        if os.pathsep in os.fspath(env_dir):
            raise ValueError(f'Refusing to create a venv in {env_dir} because '
                             f'it contains the PATH separator {os.pathsep}.')
        if os.path.exists(env_dir) and self.clear:
            self.clear_directory(env_dir)
        context = types.SimpleNamespace()
        context.env_dir = env_dir
        context.env_name = os.path.split(env_dir)[1]
        context.prompt = self.prompt if self.prompt is not None else context.env_name
        create_if_needed(env_dir)
        executable = sys._base_executable
        if not executable:  # see gh-96861
            raise ValueError('Unable to determine path to the running '
                             'Python interpreter. Provide an explicit path or '
                             'check that your PATH environment variable is '
                             'correctly set.')
        dirname, exename = os.path.split(os.path.abspath(executable))
        if sys.platform == 'win32':
            # Always create the simplest name in the venv. It will either be a
            # link back to executable, or a copy of the appropriate launcher
            _d = '_d' if os.path.splitext(exename)[0].endswith('_d') else ''
            exename = f'python{_d}.exe'
        context.executable = executable
        context.python_dir = dirname
        context.python_exe = exename
        binpath = self._venv_path(env_dir, 'scripts')
        libpath = self._venv_path(env_dir, 'purelib')
        platlibpath = self._venv_path(env_dir, 'platlib')

        # PEP 405 says venvs should create a local include directory.
        # See https://peps.python.org/pep-0405/#include-files
        # XXX: This directory is not exposed in sysconfig or anywhere else, and
        #      doesn't seem to be utilized by modern packaging tools. We keep it
        #      for backwards-compatibility, and to follow the PEP, but I would
        #      recommend against using it, as most tooling does not pass it to
        #      compilers. Instead, until we standardize a site-specific include
        #      directory, I would recommend installing headers as package data,
        #      and providing some sort of API to get the include directories.
        #      Example: https://numpy.org/doc/2.1/reference/generated/numpy.get_include.html
        incpath = os.path.join(env_dir, 'Include' if os.name == 'nt' else 'include')

        context.inc_path = incpath
        create_if_needed(incpath)
        context.lib_path = libpath
        create_if_needed(libpath)
        context.platlib_path = platlibpath
        create_if_needed(platlibpath)
        context.bin_path = binpath
        context.bin_name = os.path.relpath(binpath, env_dir)
        context.env_exe = os.path.join(binpath, exename)
        create_if_needed(binpath)
        # Assign and update the command to use when launching the newly created
        # environment, in case it isn't simply the executable script (e.g. bpo-45337)
        context.env_exec_cmd = context.env_exe
        if sys.platform == 'win32':
            # bpo-45337: Fix up env_exec_cmd to account for file system redirections.
            # Some redirects only apply to CreateFile and not CreateProcess
            real_env_exe = os.path.realpath(context.env_exe)
            if not self._same_path(real_env_exe, context.env_exe):
                logger.warning('Actual environment location may have moved due to '
                               'redirects, links or junctions.\n'
                               '  Requested location: "%s"\n'
                               '  Actual location:    "%s"',
                               context.env_exe, real_env_exe)
                context.env_exec_cmd = real_env_exe
        return context