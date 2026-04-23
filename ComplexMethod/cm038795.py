def _parse_omp_threads_bind_env(self):
        vllm_mask = envs.VLLM_CPU_OMP_THREADS_BIND
        self.skip_setup = vllm_mask == "nobind"
        self.auto_setup = vllm_mask == "auto"
        self.reserved_cpu_list = []
        self.cpu_lists = []

        if self.auto_setup:
            # auto generate CPU lists
            cpu_arch = current_platform.get_cpu_architecture()
            if cpu_arch == CpuArchEnum.POWERPC:
                # For POWERPC SMT-8/4/2
                cpu_list, reserve_list = self._get_autobind_cpu_ids(
                    lambda cpus: [cpu for cpu in cpus if cpu.id % 8 < 4]
                )
            elif cpu_arch in (CpuArchEnum.X86, CpuArchEnum.S390X):
                # For x86/S390X SMT-2, use 1 logical CPU per physical core
                cpu_list, reserve_list = self._get_autobind_cpu_ids(
                    lambda cpus: cpus[-1:]
                )
            elif cpu_arch == CpuArchEnum.ARM:
                # For AArch64, no SMT, use all logical CPU
                cpu_list, reserve_list = self._get_autobind_cpu_ids(lambda cpus: cpus)
            else:
                cpu_list, reserve_list = [], []
                raise RuntimeError(f"{cpu_arch} doesn't support auto CPU binding.")

            for item in cpu_list:
                self.cpu_lists.append([x.id for x in item])
            self.reserved_cpu_list = [x.id for x in reserve_list]
        elif not self.skip_setup:
            # user defined CPU lists
            omp_cpuids_list = vllm_mask.split("|")
            if self.local_dp_rank is not None:
                local_dp_rank = self.local_dp_rank
                world_size = self.local_world_size
                # Rank mapping [DP, PP, TP]
                omp_cpuids_list = omp_cpuids_list[
                    local_dp_rank * world_size : (local_dp_rank + 1) * world_size
                ]

            assert len(omp_cpuids_list) == self.local_world_size, (
                "Given "
                f"number of CPU id list {omp_cpuids_list} doesn't match "
                f"local world size {self.local_world_size}."
            )

            # parse CPU list strings like "5,2-4" to [5, 2, 3, 4]
            self.cpu_lists = [cr_utils.parse_id_list(s) for s in omp_cpuids_list]
        else:
            # skip
            self.cpu_lists = []

        msg = "OpenMP thread binding info: \n"
        for i in range(self.local_world_size):
            msg += f"\tlocal_rank={i}, core ids={self.cpu_lists[i]}\n"
        msg += f"\treserved_cpus={self.reserved_cpu_list}"
        logger.info(msg)