def process(self):
        """EFFMPEG Process"""
        logger.debug("Running Effmpeg")
        # Format action to match the method name
        self.args.action = self.args.action.replace("-", "_")
        logger.debug("action: '%s'", self.args.action)

        # Instantiate input DataItem object
        self.input = DataItem(path=self.args.input)

        # Instantiate output DataItem object
        self._set_output()

        # Instantiate ref_vid DataItem object
        self._set_ref_video()

        # Check that correct input and output arguments were provided
        self._check_inputs()

        # Process start and duration arguments
        self._set_times()

        # Set fps
        self._set_fps()

        # Processing transpose
        if self.args.transpose is None or \
                self.args.transpose.lower() == "none":
            self.args.transpose = None
        else:
            self.args.transpose = self.args.transpose[1]

        # Processing degrees
        if self.args.degrees is None \
                or self.args.degrees.lower() == "none" \
                or self.args.degrees == "":
            self.args.degrees = None
        elif self.args.transpose is None:
            try:
                int(self.args.degrees)
            except ValueError:
                logger.error("You have entered an invalid value for degrees: %s",
                             self.args.degrees)
                sys.exit(1)

        # Set verbosity of output
        self.__set_verbosity(self.args.quiet, self.args.verbose)

        # Set self.print_ to True if output needs to be printed to stdout
        if self.args.action in self._actions_have_print_output:
            self.print_ = True

        self.effmpeg_process()
        logger.debug("Finished Effmpeg process")