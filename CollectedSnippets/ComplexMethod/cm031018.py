def _add_ci_python_opts(self, python_opts, keep_environ):
        # --fast-ci and --slow-ci add options to Python.
        #
        # Some platforms run tests in embedded mode and cannot change options
        # after startup, so if this function changes, consider also updating:
        #  * gradle_task in Android/android.py

        # Unbuffered stdout and stderr. This isn't helpful on Android, because
        # it would cause lines to be split into multiple log messages.
        if not sys.stdout.write_through and sys.platform != "android":
            python_opts.append('-u')

        # Add warnings filter 'error', unless the user specified a different
        # filter. Ignore BytesWarning since it's controlled by '-b' below.
        if not [
            opt for opt in sys.warnoptions
            if not opt.endswith("::BytesWarning")
        ]:
            python_opts.extend(('-W', 'error'))

        # Error on bytes/str comparison
        if sys.flags.bytes_warning < 2:
            python_opts.append('-bb')

        if not keep_environ:
            # Ignore PYTHON* environment variables
            if not sys.flags.ignore_environment:
                python_opts.append('-E')