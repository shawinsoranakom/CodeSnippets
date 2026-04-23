def _ensure_dnf(self):
        locale = get_best_parsable_locale(self.module)
        os.environ["LC_ALL"] = os.environ["LC_MESSAGES"] = locale
        os.environ["LANGUAGE"] = os.environ["LANG"] = locale

        global libdnf5
        global LIBDNF5_ERRORS
        has_dnf = True
        try:
            import libdnf5  # type: ignore[import]
        except ImportError:
            has_dnf = False

        try:
            import libdnf5.exception  # type: ignore[import-not-found]
            LIBDNF5_ERRORS = (libdnf5.exception.Error, libdnf5.exception.NonLibdnf5Exception)
        except (ImportError, AttributeError):
            pass

        if has_dnf:
            return

        system_interpreters = [
            "/usr/libexec/platform-python",
            "/usr/bin/python3",
            "/usr/bin/python",
        ]

        if not has_respawned():
            for attempt in (1, 2):
                # probe well-known system Python locations for accessible bindings
                interpreter = probe_interpreters_for_module(system_interpreters, "libdnf5")
                if interpreter:
                    # respawn under the interpreter where the bindings should be found
                    respawn_module(interpreter)
                    # end of the line for this module, the process will exit here once the respawned module completes
                if attempt == 1:
                    if self.module.check_mode:
                        self.module.fail_json(
                            msg="python3-libdnf5 must be installed to use check mode. "
                                "If run normally this module can auto-install it, "
                                "see the auto_install_module_deps option.",
                        )
                    elif self.auto_install_module_deps:
                        self.module.run_command(["dnf", "install", "-y", "python3-libdnf5"], check_rc=True)
                    else:
                        break

        py_version = sys.version.replace("\n", "")
        self.module.fail_json(
            msg=f"Could not import the libdnf5 python module using {sys.executable} ({py_version}). "
            "Ensure python3-libdnf5 package is installed (either manually or via the auto_install_module_deps option) "
            f"or that you have specified the correct ansible_python_interpreter. (attempted {system_interpreters}).",
            failures=[],
        )