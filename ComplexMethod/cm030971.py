def __enter__(self):
        """On Windows, disable Windows Error Reporting dialogs using
        SetErrorMode() and CrtSetReportMode().

        On UNIX, try to save the previous core file size limit, then set
        soft limit to 0.
        """
        if sys.platform.startswith('win'):
            # see http://msdn.microsoft.com/en-us/library/windows/desktop/ms680621.aspx
            try:
                import msvcrt
            except ImportError:
                return

            self.old_value = msvcrt.GetErrorMode()

            msvcrt.SetErrorMode(self.old_value | msvcrt.SEM_NOGPFAULTERRORBOX)

            # bpo-23314: Suppress assert dialogs in debug builds.
            # CrtSetReportMode() is only available in debug build.
            if hasattr(msvcrt, 'CrtSetReportMode'):
                self.old_modes = {}
                for report_type in [msvcrt.CRT_WARN,
                                    msvcrt.CRT_ERROR,
                                    msvcrt.CRT_ASSERT]:
                    old_mode = msvcrt.CrtSetReportMode(report_type,
                            msvcrt.CRTDBG_MODE_FILE)
                    old_file = msvcrt.CrtSetReportFile(report_type,
                            msvcrt.CRTDBG_FILE_STDERR)
                    self.old_modes[report_type] = old_mode, old_file

        else:
            try:
                import resource
                self.resource = resource
            except ImportError:
                self.resource = None
            if self.resource is not None:
                try:
                    self.old_value = self.resource.getrlimit(self.resource.RLIMIT_CORE)
                    self.resource.setrlimit(self.resource.RLIMIT_CORE,
                                            (0, self.old_value[1]))
                except (ValueError, OSError):
                    pass

            if sys.platform == 'darwin':
                import subprocess
                # Check if the 'Crash Reporter' on OSX was configured
                # in 'Developer' mode and warn that it will get triggered
                # when it is.
                #
                # This assumes that this context manager is used in tests
                # that might trigger the next manager.
                cmd = ['/usr/bin/defaults', 'read',
                       'com.apple.CrashReporter', 'DialogType']
                proc = subprocess.Popen(cmd,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE)
                with proc:
                    stdout = proc.communicate()[0]
                if stdout.strip() == b'developer':
                    print("this test triggers the Crash Reporter, "
                          "that is intentional", end='', flush=True)

        return self