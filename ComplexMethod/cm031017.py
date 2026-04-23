def _add_cross_compile_opts(self, regrtest_opts):
        # WASM/WASI buildbot builders pass multiple PYTHON environment
        # variables such as PYTHONPATH and _PYTHON_HOSTRUNNER.
        keep_environ = bool(self.python_cmd)
        environ = None

        # Are we using cross-compilation?
        cross_compile = is_cross_compiled()

        # Get HOSTRUNNER
        hostrunner = get_host_runner()

        if cross_compile:
            # emulate -E, but keep PYTHONPATH + cross compile env vars,
            # so test executable can load correct sysconfigdata file.
            keep = {
                '_PYTHON_PROJECT_BASE',
                '_PYTHON_HOST_PLATFORM',
                '_PYTHON_SYSCONFIGDATA_NAME',
                "_PYTHON_SYSCONFIGDATA_PATH",
                'PYTHONPATH'
            }
            old_environ = os.environ
            new_environ = {
                name: value for name, value in os.environ.items()
                if not name.startswith(('PYTHON', '_PYTHON')) or name in keep
            }
            # Only set environ if at least one variable was removed
            if new_environ != old_environ:
                environ = new_environ
            keep_environ = True

        if cross_compile and hostrunner:
            if self.num_workers == 0 and not self.single_process:
                # For now use only two cores for cross-compiled builds;
                # hostrunner can be expensive.
                regrtest_opts.extend(['-j', '2'])

            # If HOSTRUNNER is set and -p/--python option is not given, then
            # use hostrunner to execute python binary for tests.
            if not self.python_cmd:
                buildpython = sysconfig.get_config_var("BUILDPYTHON")
                python_cmd = f"{hostrunner} {buildpython}"
                regrtest_opts.extend(["--python", python_cmd])
                keep_environ = True

        return (environ, keep_environ)