def start_processes(
    fn,
    args=(),
    nprocs=1,
    join=True,
    daemon=False,
    start_method="spawn",
):
    # To speed up performance in certain cases (see https://github.com/pytorch/pytorch/issues/133010),
    # this func will start processes in parallel if start_method is 'forkserver'.
    # Please opt in to this perf optimization by setting env var (TORCH_MP_PARALLEL_START) to 1.
    # todo: investigate why spawn does not work with threadpool and raises SIGINT
    if (
        start_method == "forkserver"
        and os.environ.get(ENV_VAR_PARALLEL_START, "0") == "1"
    ):
        log.info("Starting processes in parallel.")
        start_parallel = True
    else:
        # Set env var TORCH_MP_PARALLEL_START to 0 to disable parallel start
        start_parallel = False

    mp = multiprocessing.get_context(start_method)
    error_files = [None] * nprocs
    processes = [None] * nprocs

    def start_process(i):
        # Each process is assigned a file to write tracebacks to.  We
        # use the file being non-empty to indicate an exception
        # occurred (vs an expected shutdown).  Note: this previously
        # used a multiprocessing.Queue but that can be prone to
        # deadlocks, so we went with a simpler solution for a one-shot
        # message between processes.
        tf = tempfile.NamedTemporaryFile(  # noqa: SIM115
            prefix="pytorch-errorfile-", suffix=".pickle", delete=False
        )
        tf.close()
        os.unlink(tf.name)

        process = mp.Process(  # pyrefly: ignore  # missing-attribute
            target=_wrap,
            args=(fn, i, args, tf.name),
            daemon=daemon,
        )

        process.start()
        return i, process, tf.name

    if not start_parallel:
        for i in range(nprocs):
            idx, process, tf_name = start_process(i)
            error_files[idx] = tf_name
            processes[idx] = process
    else:
        with ThreadPoolExecutor(max_workers=nprocs) as executor:
            futures = [executor.submit(start_process, i) for i in range(nprocs)]
            for fut in as_completed(futures):
                idx, process, tf_name = fut.result()
                # idx and process rank needs to be the same.
                error_files[idx] = tf_name
                processes[idx] = process
    context = ProcessContext(processes, error_files)
    if not join:
        return context

    # Loop on join until it returns True or raises an exception.
    while not context.join():
        pass