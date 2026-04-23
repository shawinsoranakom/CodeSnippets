def gen_cli_arguments(self, command: str) -> T.Generator[tuple[str, ...], None, None]:
        """ Yield the generated cli arguments for the selected command

        Parameters
        ----------
        command: str
            The command to generate the command line arguments for

        Yields
        ------
        tuple[str, ...]
            The generated command line arguments
        """
        output_dir = None
        switches = ""
        args = []
        for _, option in self._gen_command_options(command):
            str_val = str(option.cpanel_option.get())
            switch = option.opts[0]
            batch_mode = command == "extract" and switch == "-b"  # Check for batch mode
            if command in ("extract", "convert") and switch == "-o":  # Output location for preview
                output_dir = str_val

            if str_val in ("False", ""):  # skip no value opts
                continue

            if str_val == "True":  # store_true just output the switch
                switches += switch[1:]
                continue

            if option.nargs is not None:
                if "\"" in str_val:
                    val = [arg[1:-1] for arg in re.findall(r"\".+?\"", str_val)]
                else:
                    val = str_val.split(" ")
                arg = (switch, *val)
            else:
                arg = (switch, str_val)
            args.append(arg)

        switch_args = [] if not switches else [(f"-{switches}", )]
        yield from switch_args + args

        if command in ("extract", "convert") and output_dir is not None:
            get_images().preview_extract.set_faceswap_output_path(output_dir,
                                                                  batch_mode=batch_mode)