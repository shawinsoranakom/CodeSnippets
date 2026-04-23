def _build_args(self,
                    category: str,
                    command: str | None = None,
                    generate: bool = False) -> list[str]:
        """ Build the faceswap command and arguments list.

        If training, pass the model folder and name to the training
        :class:`lib.gui.analysis.Session` for the GUI.

        Parameters
        ----------
        category: str, ["faceswap", "tools"]
            The script that is executing the command
        command: str, optional
            The main faceswap command to execute, if provided. The currently running task if
            ``None``. Default: ``None``
        generate: bool, optional
            ``True`` if the command is just to be generated for display. ``False`` if the command
            is to be executed

        Returns
        -------
        list[str]
            The full faceswap command to be executed or displayed
        """
        logger.debug("Build cli arguments: (category: %s, command: %s, generate: %s)",
                     category, command, generate)
        command = self._command if not command else command
        assert command is not None
        script = f"{category}.py"
        pathexecscript = os.path.join(os.path.realpath(os.path.dirname(sys.argv[0])), script)

        args = [sys.executable] if generate else [sys.executable, "-u"]
        args.extend([pathexecscript, command])

        cli_opts = get_config().cli_opts
        for cliopt in cli_opts.gen_cli_arguments(command):
            args.extend(cliopt)
            if command == "train" and not generate:
                self._get_training_session_info(cliopt)

        if not generate:
            args.append("-G")  # Indicate to Faceswap that we are running the GUI
        if generate:
            # Delimit args with spaces
            args = [f'"{arg}"' if " " in arg and not arg.startswith(("[", "("))
                    and not arg.endswith(("]", ")")) else arg
                    for arg in args]
        logger.debug("Built cli arguments: (%s)", args)
        return args