def reify(
        self,
        envs: dict[int, dict[str, str]],
    ) -> LogsDest:
        """
        Uses following scheme to build log destination paths:

        - `<log_dir>/<rdzv_run_id>/attempt_<attempt>/<rank>/stdout.log`
        - `<log_dir>/<rdzv_run_id>/attempt_<attempt>/<rank>/stderr.log`
        - `<log_dir>/<rdzv_run_id>/attempt_<attempt>/<rank>/error.json`
        - `<log_dir>/<rdzv_run_id>/attempt_<attempt>/filtered_stdout.log`
        - `<log_dir>/<rdzv_run_id>/attempt_<attempt>/filtered_stderr.log`
        """
        nprocs = len(envs)
        global_env = {}  # use only to query properties that are not dependent on a rank
        if nprocs > 0:
            global_env = envs[0]
        else:
            logger.warning(
                "Empty envs map provided when defining logging destinations."
            )
        # Keys are always defined, but values can be missing in unit tests
        run_id = global_env.get("TORCHELASTIC_RUN_ID", "test_run_id")
        restart_count = global_env.get("TORCHELASTIC_RESTART_COUNT", "0")

        attempt_log_dir: str = ""
        if self._root_log_dir != os.devnull:
            if not self._run_log_dir:
                self._run_log_dir = self._make_log_dir(self._root_log_dir, run_id)

            attempt_log_dir = os.path.join(
                self._run_log_dir, f"attempt_{restart_count}"
            )  # type: ignore[call-overload]
            shutil.rmtree(attempt_log_dir, ignore_errors=True)
            os.makedirs(attempt_log_dir)

        if self._root_log_dir == os.devnull:
            attempt_log_dir = os.devnull

        # create subdirs for each local rank in the logs_dir
        # logs_dir
        #       |- 0
        #          |- error.json
        #          |- stdout.log
        #          |- stderr.log
        #       |- ...
        #       |- (nprocs-1)
        redirs = to_map(self._redirects, nprocs)
        ts = to_map(self._tee, nprocs)

        # to tee stdout/stderr we first redirect into a file
        # then tail -f stdout.log/stderr.log so add tee settings to redirects
        for local_rank, tee_std in ts.items():
            redirect_std = redirs[local_rank]
            redirs[local_rank] = redirect_std | tee_std

        SYS_STREAM = ""  # special case to indicate to output to console
        stdouts = dict.fromkeys(range(nprocs), SYS_STREAM)
        stderrs = dict.fromkeys(range(nprocs), SYS_STREAM)
        tee_stdouts: dict[int, str] = {}
        tee_stderrs: dict[int, str] = {}
        error_files = {}

        for local_rank in range(nprocs):
            if attempt_log_dir == os.devnull:
                tee_stdouts[local_rank] = os.devnull
                tee_stderrs[local_rank] = os.devnull
                error_files[local_rank] = os.devnull
                envs[local_rank]["TORCHELASTIC_ERROR_FILE"] = ""
            else:
                clogdir = os.path.join(attempt_log_dir, str(local_rank))
                os.mkdir(clogdir)

                rd = redirs[local_rank]
                if (rd & Std.OUT) == Std.OUT:
                    stdouts[local_rank] = os.path.join(clogdir, "stdout.log")
                if (rd & Std.ERR) == Std.ERR:
                    stderrs[local_rank] = os.path.join(clogdir, "stderr.log")

                t = ts[local_rank]
                if t & Std.OUT == Std.OUT:
                    tee_stdouts[local_rank] = stdouts[local_rank]
                if t & Std.ERR == Std.ERR:
                    tee_stderrs[local_rank] = stderrs[local_rank]

                if (
                    self._local_ranks_filter
                    and local_rank not in self._local_ranks_filter
                ):
                    # If stream is tee'd, only write to file, but don't tail
                    if local_rank in tee_stdouts:
                        tee_stdouts.pop(local_rank, None)
                    if local_rank in tee_stderrs:
                        tee_stderrs.pop(local_rank, None)

                    # If stream is not redirected, don't print
                    if stdouts[local_rank] == SYS_STREAM:
                        stdouts[local_rank] = os.devnull
                    if stderrs[local_rank] == SYS_STREAM:
                        stderrs[local_rank] = os.devnull

                error_file = os.path.join(clogdir, "error.json")
                # pyrefly: ignore [unsupported-operation]
                error_files[local_rank] = error_file
                logger.info(
                    "Setting worker%s reply file to: %s", local_rank, error_file
                )
                envs[local_rank]["TORCHELASTIC_ERROR_FILE"] = error_file

        return LogsDest(
            stdouts,
            stderrs,
            tee_stdouts,
            tee_stderrs,
            # pyrefly: ignore [bad-argument-type]
            error_files,
            os.path.join(attempt_log_dir, "filtered_stdout.log"),
            os.path.join(attempt_log_dir, "filtered_stderr.log"),
        )