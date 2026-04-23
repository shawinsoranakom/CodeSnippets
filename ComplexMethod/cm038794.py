def configure_omp_envs(self, rank: int, local_rank: int):
        if not current_platform.is_cpu() or self.skip_setup:
            yield
            return

        envs_dict = {}
        cpu_list = [str(i) for i in self.cpu_lists[local_rank]]
        envs_dict["OMP_NUM_THREADS"] = str(len(cpu_list))
        if self.use_iomp:
            # set IOMP envs
            cpu_list_str = ",".join(cpu_list)
            envs_dict["KMP_AFFINITY"] = (
                f"granularity=fine,explicit,proclist=[{cpu_list_str}]"
            )
            # The time(milliseconds) that a thread should wait after
            # completing the execution of a parallel region, before sleeping.
            envs_dict["KMP_BLOCKTIME"] = "1"
            # Prevents the CPU to run into low performance state
            envs_dict["KMP_TPAUSE"] = "0"
            # Provides fine granularity parallelism
            envs_dict["KMP_FORKJOIN_BARRIER_PATTERN"] = "dist,dist"
            envs_dict["KMP_PLAIN_BARRIER_PATTERN"] = "dist,dist"
            envs_dict["KMP_REDUCTION_BARRIER_PATTERN"] = "dist,dist"
        elif self.use_gomp:
            # set GOMP envs
            # likes '0 1 2 ...'
            cpu_list_str = " ".join(cpu_list)
            envs_dict["GOMP_CPU_AFFINITY"] = cpu_list_str
        else:
            # set OMP envs
            # likes '{0,1,2,...}'
            cpu_list_str = ",".join(cpu_list)
            envs_dict["OMP_PLACES"] = f"{{{cpu_list_str}}}"
            envs_dict["OMP_PROC_BIND"] = "true"

        # backup envs
        old_envs_dict = {}
        for k in envs_dict:
            old_envs_dict[k] = os.environ.get(k)

        try:
            # set envs
            for k, v in envs_dict.items():
                os.environ[k] = v
            yield
        finally:
            # restore old envs
            for k, v in old_envs_dict.items():  # type: ignore
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v