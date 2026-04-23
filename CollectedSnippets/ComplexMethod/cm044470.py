def execute_script(self, arguments: argparse.Namespace) -> None:
        """Performs final set up and launches the requested :attr:`_command` with the given
        command line arguments.

        Monitors for errors and attempts to shut down the process cleanly on exit.

        Parameters
        ----------
        arguments
            The command line arguments to be passed to the executing script.
        """
        is_gui = hasattr(arguments, "redirect_gui") and arguments.redirect_gui
        log_setup(arguments.loglevel, arguments.logfile, self._command, is_gui)
        success = False

        if self._command != "gui":
            self._configure_backend(arguments)
        try:
            script = self._import_script()
            process = script(arguments)
            process.process()
            success = True
        except FaceswapError as err:
            for line in str(err).splitlines():
                logger.error(line)
        except KeyboardInterrupt:  # pylint:disable=try-except-raise
            raise
        except SystemExit:
            pass
        except Exception:  # pylint:disable=broad-except
            crash_file = crash_log()
            logger.exception("Got Exception on main handler:")
            logger.critical("An unexpected crash has occurred. Crash report written to '%s'. "
                            "You MUST provide this file if seeking assistance. Please verify you "
                            "are running the latest version of faceswap before reporting",
                            crash_file)

        finally:
            safe_shutdown(got_error=not success)