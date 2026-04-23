def _init_profile_batch(self, profile_batch):
        """Validate profile_batch value and set the range of batches to profile.

        Sets values of _start_batch and _stop_batch attributes,
        specifying the start and stop batch to profile.
        Setting `profile_batch=0` disables profiling.

        Args:
          profile_batch: The range of batches to profile. Should be a
            non-negative integer or a comma separated string of pair of positive
            integers. A pair of positive integers signify a range of batches to
            profile.

        Raises:
          ValueError: If profile_batch is not an integer or a comma separated
            pair of positive integers.

        """
        profile_batch_error_message = (
            "profile_batch must be a non-negative integer or "
            "2-tuple of positive "
            "integers. A pair of positive integers "
            "signifies a range of batches "
            f"to profile. Found: {profile_batch}"
        )

        # Support legacy way of specifying "start,stop" or "start" as str.
        if isinstance(profile_batch, str):
            profile_batch = str(profile_batch).split(",")
            profile_batch = tree.map_structure(int, profile_batch)

        if isinstance(profile_batch, int):
            self._start_batch = profile_batch
            self._stop_batch = profile_batch
        elif (
            isinstance(profile_batch, (tuple, list)) and len(profile_batch) == 2
        ):
            self._start_batch, self._stop_batch = profile_batch
        else:
            raise ValueError(profile_batch_error_message)

        if self._start_batch < 0 or self._stop_batch < self._start_batch:
            raise ValueError(profile_batch_error_message)

        # True when the profiler was successfully started by this callback.
        # We track the status here to make sure callbacks do not interfere with
        # each other. The callback will only stop the profiler it started.
        self._profiler_started = False
        self._batch_trace_context = None

        if self._start_batch > 0:
            # Warm up and improve the profiling accuracy.
            self._start_profiler(logdir="")
            self._stop_profiler(save=False)
        # True when a trace is running.
        self._is_tracing = False

        # Setting `profile_batch=0` disables profiling.
        self._should_trace = not (
            self._start_batch == 0 and self._stop_batch == 0
        )