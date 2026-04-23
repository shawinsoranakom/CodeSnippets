def cli_executor(cls, args=None):
        if args is None:
            args = sys.argv

        try:
            display.debug("starting run")

            ansible_dir = Path(C.ANSIBLE_HOME).expanduser()
            try:
                ansible_dir.mkdir(mode=0o700, exist_ok=True)
            except OSError as ex:
                display.error_as_warning(f"Failed to create the directory {ansible_dir!r}.", ex)
            else:
                display.debug("Created the '%s' directory" % ansible_dir)

            cli = cls(args)
            exit_code = cli.run()
        except AnsibleError as ex:
            display.error(ex)
            exit_code = ex._exit_code
        except KeyboardInterrupt:
            display.error("User interrupted execution")
            exit_code = ExitCode.KEYBOARD_INTERRUPT
        except Exception as ex:
            try:
                raise AnsibleError("Unexpected Exception, this is probably a bug.") from ex
            except AnsibleError as ex2:
                # DTFIX-FUTURE: clean this up so we're not hacking the internals- re-wrap in an AnsibleCLIUnhandledError that always shows TB, or?
                from ansible.module_utils._internal import _traceback
                _traceback._is_traceback_enabled = lambda *_args, **_kwargs: True
                display.error(ex2)
                exit_code = ExitCode.UNKNOWN_ERROR

        sys.exit(exit_code)