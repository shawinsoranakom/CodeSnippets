def compute_num_jobs(self):
        # `num_jobs` is either the value of the MAX_JOBS environment variable
        # (if defined) or the number of CPUs available.
        num_jobs = envs.MAX_JOBS
        if num_jobs is not None:
            num_jobs = int(num_jobs)
            logger.info("Using MAX_JOBS=%d as the number of jobs.", num_jobs)
        else:
            try:
                # os.sched_getaffinity() isn't universally available, so fall
                #  back to os.cpu_count() if we get an error here.
                num_jobs = len(os.sched_getaffinity(0))
            except AttributeError:
                num_jobs = os.cpu_count()

        nvcc_threads = None
        if _is_cuda() and CUDA_HOME is not None:
            try:
                nvcc_version = get_nvcc_cuda_version()
                if nvcc_version >= Version("11.2"):
                    # `nvcc_threads` is either the value of the NVCC_THREADS
                    # environment variable (if defined) or 1.
                    # when it is set, we reduce `num_jobs` to avoid
                    # overloading the system.
                    nvcc_threads = envs.NVCC_THREADS
                    if nvcc_threads is not None:
                        nvcc_threads = int(nvcc_threads)
                        logger.info(
                            "Using NVCC_THREADS=%d as the number of nvcc threads.",
                            nvcc_threads,
                        )
                    else:
                        nvcc_threads = 1
                    num_jobs = max(1, num_jobs // nvcc_threads)
            except Exception as e:
                logger.warning("Failed to get NVCC version: %s", e)

        return num_jobs, nvcc_threads