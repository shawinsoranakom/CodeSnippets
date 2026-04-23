def target(self, choice: TritonTemplateCaller) -> float:
        """
        Entry point for the thread-pool helper threads: Wait for an open TuningProcess,
        remove it from the queue, execute the benchmark in that subprocess, and return
        the TuningProcess to the queue.
        """
        assert choice.bmreq is not None

        env_vars = ["TORCHINDUCTOR_CACHE_DIR", "TRITON_CACHE_DIR"]
        extra_env = {v: os.environ[v] for v in env_vars if v in os.environ}
        process = self.process_queue.get()
        process.put(choice.bmreq.benchmark, extra_env=extra_env)
        try:
            return process.get(
                config.max_autotune_subproc_result_timeout_seconds,
            )
        except TimeoutError:
            warnings.warn(
                f"Timed out benchmarking choice '{choice}'. It will be ignored. "
                "Please debug the root cause in case the choice can bring perf gains."
            )
            # Set to INF so this choice will be ignored
            return float("inf")
        except Exception as process_exception:
            warnings.warn(
                f"Failed to benchmark choice '{choice}'. It will be ignored. "
                "Please debug the root cause in case the choice can bring perf gains."
            )
            # Sticky CUDA errors corrupt the context, making it unrecoverable.
            # The process must be restarted to restore CUDA functionality.
            error_msg = str(process_exception)
            if (
                "cudaErrorLaunchFailure" in error_msg
                or "cudaErrorIllegalAddress" in error_msg
            ):
                process.restart()
            # Set to INF so this choice will be ignored
            return float("inf")
        finally:
            self.process_queue.put(process)