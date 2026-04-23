def launch(self, args):
        cores = []
        set_kmp_affinity = True
        enable_taskset = False
        if args.core_list:  # user specify what cores will be used by params
            cores = [int(x) for x in args.core_list.split(",")]
            if args.ncores_per_instance == -1:
                raise RuntimeError(
                    'please specify the "--ncores-per-instance" if you have pass the --core-list params'
                )
            elif (
                args.ninstances > 1
                and args.ncores_per_instance * args.ninstances < len(cores)
            ):
                logger.warning(
                    "only first %s cores will be used, \
but you specify %s cores in core_list",
                    args.ncores_per_instance * args.ninstances,
                    len(cores),
                )
            else:
                args.ninstances = len(cores) // args.ncores_per_instance

        else:
            if args.use_logical_core:
                if args.node_id != -1:
                    cores = self.cpuinfo.get_node_logical_cores(args.node_id)
                else:
                    cores = self.cpuinfo.get_all_logical_cores()
                    # When using all cores on all nodes, including logical cores,
                    # setting KMP_AFFINITY disables logical cores. Thus, KMP_AFFINITY should not be set.
                    set_kmp_affinity = False
            else:
                if args.node_id != -1:
                    cores = self.cpuinfo.get_node_physical_cores(args.node_id)
                else:
                    cores = self.cpuinfo.get_all_physical_cores()
            if (
                not args.multi_instance
                and args.ninstances == -1
                and args.ncores_per_instance == -1
            ):
                args.ninstances = 1
                args.ncores_per_instance = len(cores)
            elif (
                args.multi_instance
                and args.ninstances == -1
                and args.ncores_per_instance == -1
            ):
                args.throughput_mode = True
            elif args.ncores_per_instance == -1 and args.ninstances != -1:
                if args.ninstances > len(cores):
                    raise RuntimeError(
                        f"there are {len(cores)} total cores but you specify {args.ninstances} ninstances; \
please make sure ninstances <= total_cores)"
                    )
                else:
                    args.ncores_per_instance = len(cores) // args.ninstances
            elif args.ncores_per_instance != -1 and args.ninstances == -1:
                if not args.skip_cross_node_cores:
                    args.ninstances = len(cores) // args.ncores_per_instance
                else:
                    ncore_per_node = len(self.cpuinfo.node_physical_cores[0])
                    num_leftover_cores = ncore_per_node % args.ncores_per_instance
                    if args.ncores_per_instance > ncore_per_node:
                        # too many ncores_per_instance to skip cross-node cores
                        logger.warning(
                            "there are %s core(s) per socket, but you specify %s ncores_per_instance and \
skip_cross_node_cores. Please make sure --ncores-per-instance < core(s) per \
socket",
                            ncore_per_node,
                            args.ncores_per_instance,
                        )
                        sys.exit(-1)
                    elif num_leftover_cores == 0:
                        # aren't any cross-node cores
                        logger.info(
                            "--skip-cross-node-cores is set, but there are no cross-node cores."
                        )
                        args.ninstances = len(cores) // args.ncores_per_instance
                    else:
                        # skip cross-node cores
                        if args.ninstances != -1:
                            logger.warning(
                                "--skip-cross-node-cores is exclusive to --ninstances. --ninstances \
won't take effect even if it is set explicitly."
                            )

                        i = 1
                        leftover_cores = set()
                        while ncore_per_node * i <= len(cores):
                            leftover_cores.update(
                                cores[
                                    ncore_per_node * i
                                    - num_leftover_cores : ncore_per_node * i
                                ]
                            )
                            i += 1
                        cores = list(set(cores) - leftover_cores)
                        if len(cores) % args.ncores_per_instance != 0:
                            raise AssertionError(
                                f"Number of cores ({len(cores)}) must be divisible by "
                                f"ncores_per_instance ({args.ncores_per_instance})"
                            )
                        args.ninstances = len(cores) // args.ncores_per_instance
            else:
                if args.ninstances * args.ncores_per_instance > len(cores):
                    raise RuntimeError(
                        "Please make sure ninstances * ncores_per_instance <= total_cores"
                    )
            if args.latency_mode:
                logger.warning(
                    "--latency-mode is exclusive to --ninstances, --ncores-per-instance, --node-id and \
--use-logical-core. They won't take effect even they are set explicitly."
                )
                args.ncores_per_instance = 4
                cores = self.cpuinfo.get_all_physical_cores()
                args.ninstances = len(cores) // args.ncores_per_instance

            if args.throughput_mode:
                logger.warning(
                    "--throughput-mode is exclusive to --ninstances, --ncores-per-instance, --node-id and \
--use-logical-core. They won't take effect even they are set explicitly."
                )
                args.ninstances = self.cpuinfo.node_nums
                cores = self.cpuinfo.get_all_physical_cores()
                args.ncores_per_instance = len(cores) // args.ninstances

        if args.ninstances > 1 and args.rank != -1:
            logger.info(
                "assigning %s cores for instance %s",
                args.ncores_per_instance,
                args.rank,
            )

        if not args.disable_numactl:
            numactl_available = self.is_numactl_available()
            if not numactl_available:
                if not args.disable_taskset:
                    logger.warning(
                        "Core binding with numactl is not available. Disabling numactl and using taskset instead. \
                    This may affect performance in multi-socket system; please use numactl if memory binding is needed."
                    )
                    args.disable_numactl = True
                    enable_taskset = True
                else:
                    logger.warning(
                        "Core binding with numactl is not available, and --disable_taskset is set. \
                    Please unset --disable_taskset to use taskset instead of numactl."
                    )
                    sys.exit(-1)

        if not args.disable_taskset:
            enable_taskset = True

        self.set_multi_thread_and_allocator(
            args.ncores_per_instance,
            args.disable_iomp,
            set_kmp_affinity,
            args.enable_tcmalloc,
            args.enable_jemalloc,
            args.use_default_allocator,
        )
        entrypoint = ""
        launch_args = {}
        launch_envs: dict[int, dict] = {}
        launch_tee = {}
        # check whether is launched from torchrun with --nproc-per-node <num workers>
        local_size = int(os.environ.get("LOCAL_WORLD_SIZE", 1))
        local_rank = int(os.environ.get("LOCAL_RANK", 0))
        for i in range(args.ninstances):
            cmd = []
            cur_process_cores = ""
            if not args.disable_numactl or enable_taskset:
                if not args.disable_numactl:
                    cmd = ["numactl"]
                elif enable_taskset:
                    cmd = ["taskset"]
                cores = sorted(cores)
                if (
                    args.rank == -1
                ):  # sequentially assign ncores_per_instance to ninstances
                    core_list = cores[
                        i * args.ncores_per_instance : (i + 1)
                        * args.ncores_per_instance
                    ]
                else:  # assign ncores_per_instance from rank
                    core_list = cores[
                        args.rank * args.ncores_per_instance : (args.rank + 1)
                        * args.ncores_per_instance
                    ]

                core_ranges: list[dict] = []
                if local_size > 1:
                    total_num_cores = len(core_list)
                    cores_per_rank = total_num_cores // local_size
                    if cores_per_rank < 1:
                        raise AssertionError(
                            f"At least one core needs to be assigned to each rank, "
                            f"got {total_num_cores} cores for {local_size} ranks"
                        )
                    core_list = core_list[
                        cores_per_rank * local_rank : cores_per_rank * (local_rank + 1)
                    ]
                for core in core_list:
                    if len(core_ranges) == 0:
                        range_elem = {"start": core, "end": core}
                        core_ranges.append(range_elem)
                    else:
                        if core - core_ranges[-1]["end"] == 1:
                            core_ranges[-1]["end"] = core
                        else:
                            range_elem = {"start": core, "end": core}
                            core_ranges.append(range_elem)
                for r in core_ranges:
                    cur_process_cores = f"{cur_process_cores}{r['start']}-{r['end']},"
                cur_process_cores = cur_process_cores[:-1]
                if not args.disable_numactl:
                    numa_params = f"-C {cur_process_cores} "
                    numa_ids = ",".join(
                        [
                            str(numa_id)
                            for numa_id in self.cpuinfo.numa_aware_check(core_list)
                        ]
                    )
                    numa_params += f"-m {numa_ids}"
                    cmd.extend(numa_params.split())
                elif enable_taskset:
                    taskset_params = f"-c {cur_process_cores} "
                    cmd.extend(taskset_params.split())
            with_python = not args.no_python
            if with_python:
                cmd.append(sys.executable)
                cmd.append("-u")
            if args.module:
                cmd.append("-m")
            cmd.append(args.program)
            cmd.extend(args.program_args)
            cmd_s = " ".join(cmd)
            logger.info(cmd_s)
            if entrypoint == "":
                entrypoint = cmd[0]
            del cmd[0]
            launch_args[i] = tuple(cmd)
            launch_envs[i] = {}
            launch_tee[i] = Std.ALL

            if args.rank != -1:  # launches single instance, rank, only
                break

        ctx = start_processes(
            name=args.log_file_prefix,
            entrypoint=entrypoint,
            args=launch_args,
            envs=launch_envs,
            logs_specs=_DefaultLogsSpecs(log_dir=args.log_path, tee=launch_tee),
        )
        ctx.wait()