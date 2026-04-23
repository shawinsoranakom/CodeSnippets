def _load_pipeline(self, arguments: Namespace) -> ExtractRunner:  # noqa[C901]
        """ Create the extraction pipeline and run profiling, if selected

        Parameters
        ---------
        arguments
            The arguments generated from Faceswap's command line arguments

        Returns
        -------
        The final runner, with input interfaces, from the pipeline
        """
        retval = None
        conf_file = arguments.config_file
        profile = arguments.benchmark
        try:
            if arguments.detector != "file":
                retval = Detect(arguments.detector,
                                rotation=arguments.rotate_images,
                                min_size=arguments.min_size,
                                max_size=arguments.max_size,
                                compile_model=arguments.compile,
                                config_file=conf_file)(retval, profile=profile)
            if arguments.aligner != "file":
                retval = Align(arguments.aligner,
                               re_feeds=arguments.re_feed,
                               re_align=arguments.re_align,
                               normalization=arguments.normalization,
                               filters=arguments.align_filters,
                               compile_model=arguments.compile,
                               config_file=conf_file)(retval, profile=profile)
            if arguments.masker is not None:
                for masker in arguments.masker:
                    retval = Mask(masker,
                                  compile_model=arguments.compile,
                                  config_file=conf_file)(retval, profile=profile)
            if arguments.identity:
                for idx, identity in enumerate(arguments.identity):
                    retval = Identity(identity,
                                      self._face_filter.threshold,
                                      compile_model=arguments.compile,
                                      config_file=conf_file)(retval, profile=profile)
                    if self._face_filter.enabled and idx == 0:
                        # Add the first selected identity plugin
                        self._face_filter.add_identity_plugin(retval)

            if retval is not None and profile:
                Profiler(retval)()

            retval = File()() if retval is None else retval

        except Exception:
            logger.debug("[Extract] Error during pipeline initialization")
            if retval is not None:
                retval.stop()
            raise
        logger.debug("[Extract] Pipeline output: %s", retval)
        return retval