def _assign_worker_ranks(
        self, store, group_rank: int, group_world_size: int, spec: WorkerSpec
    ) -> list[Worker]:
        """Determine proper ranks for worker processes.

        Fast Path: when all workers have the same role and world size. We calculate
        the global rank to be group_rank * group_world_size + local_rank. And the
        `role_world_size` is the same as `global_world_size`. No TCP store is used in
        this case. This is only enabled when users set the environment variable
        `TORCH_ELASTIC_WORKER_IDENTICAL` to 1.

        Time complexity: each worker O(1), overall O(1)

        Slow Path: when workers have different roles and world sizes. We use the
        the following algorithm:

        1. Each agent writes its configuration(group_rank, group_world_size
           , num_workers) to the common store.
        2. The rank 0 agent reads all the role_info from the store and
           determines each agents worker ranks.
        3. Determine the global rank: the global rank of the workers is computed
           by cumulative sum of the local_world_size for all workers in front of it.
           For efficiency reasons each worker is assigned a base global rank
           such that it's workers are in the range [base_global_rank,
           base_global_rank + local_world_size).
        4. Determine the role rank: The role rank is determined using the algorithms
           in the point 3 with the exception that the ranks are calculated with
           respect to the role name.
        5. The rank 0 agent writes the assigned ranks to the store.
        6. Each agent reads the assigned ranks from the store.

        Time complexity: each worker O(1), rank0 O(n), overall O(n)
        """

        if os.environ.get("TORCH_ELASTIC_WORKER_IDENTICAL", "0") == "1":
            global_world_size = group_world_size * spec.local_world_size
            base_global_rank = group_rank * spec.local_world_size
            base_role_rank = base_global_rank
            role_world_size = global_world_size
        else:
            ROLE_INFO_PREFIX = "torchelastic/role_info/"
            ASSIGNED_RANKS_PREFIX = "torchelastic/assigned_ranks/"

            agent_role_info = _RoleInstanceInfo(
                spec.role, group_rank, spec.local_world_size
            )
            store.set(f"{ROLE_INFO_PREFIX}{group_rank}", agent_role_info.serialize())

            # tcp store is collocated with rank 0 so we can use it to do extra compute to reduce overall # of operations.
            if group_rank == 0:
                role_infos_bytes = store.multi_get(
                    [f"torchelastic/role_info/{i}" for i in range(group_world_size)]
                )
                role_infos = [
                    _RoleInstanceInfo.deserialize(info_bytes)
                    for info_bytes in role_infos_bytes
                ]

                role_sizes = defaultdict(lambda: 0)
                global_size = 0
                for role_info in role_infos:
                    role_sizes[role_info.role] += role_info.local_world_size
                    global_size += role_info.local_world_size

                base_global_rank = 0
                role_ranks = defaultdict(lambda: 0)

                keys = []
                values = []
                for i, role_info in enumerate(role_infos):
                    keys.append(f"{ASSIGNED_RANKS_PREFIX}{i}")
                    values.append(
                        json.dumps(
                            [
                                base_global_rank,
                                global_size,
                                role_ranks[role_info.role],
                                role_sizes[role_info.role],
                            ]
                        )
                    )

                    base_global_rank += role_info.local_world_size
                    role_ranks[role_info.role] += role_info.local_world_size

                store.multi_set(keys, values)

            # get will block until the data is available in the store.
            (
                base_global_rank,
                global_world_size,
                base_role_rank,
                role_world_size,
            ) = json.loads(store.get(f"{ASSIGNED_RANKS_PREFIX}{group_rank}"))

        workers = []
        for local_rank in range(spec.local_world_size):
            worker = Worker(
                local_rank=local_rank,
                global_rank=base_global_rank + local_rank,
                role_rank=base_role_rank + local_rank,
                world_size=global_world_size,
                role_world_size=role_world_size,
            )
            workers.append(worker)
        return workers