def discover_numa_topology(cls) -> list[list[int]]:
        """
        Discover NUMA topology and keep the last physical core of each numa
        into one core group list for nixl start_kv_load()
        """
        SYS_NODE = "/sys/devices/system/node"
        SYS_CPU = "/sys/devices/system/cpu"

        if not (os.path.exists(SYS_NODE) and os.path.exists(SYS_CPU)):
            return []

        core_rsv_for_kv = []
        for node in os.listdir(SYS_NODE):
            if not node.startswith("node") or not node[4:].isdigit():
                continue
            node_path = f"{SYS_NODE}/{node}"

            seen_phys = set()
            for cpu in os.listdir(node_path):
                if not cpu.startswith("cpu") or not cpu[3:].isdigit():
                    continue

                cpu_id = int(cpu[3:])
                # thread_siblings based on cpu_id
                path = f"{SYS_CPU}/cpu{cpu_id}/topology/thread_siblings_list"

                if os.path.exists(path):
                    try:
                        with open(path) as f:
                            s = f.read()
                        cpus: list[int] = []
                        for part in s.strip().split(","):
                            if "-" in part:
                                a, b = map(int, part.split("-"))
                                cpus.extend(range(a, b + 1))
                            else:
                                cpus.append(int(part))
                        siblings = cpus if cpus else [cpu_id]
                    except (OSError, ValueError):
                        siblings = [cpu_id]
                else:
                    siblings = [cpu_id]

                phys = min(siblings)

                if phys not in seen_phys:
                    seen_phys.add(phys)

            if len(seen_phys) > 0:
                core_rsv_for_kv.append(list(seen_phys))

        return core_rsv_for_kv