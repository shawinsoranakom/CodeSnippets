def get_container_stats(self, container_name: str) -> DockerContainerStats:
        try:
            container = self.client().containers.get(container_name)
            sdk_stats = container.stats(stream=False)

            # BlockIO: (Read, Write) bytes
            read_bytes = 0
            write_bytes = 0
            for entry in (
                sdk_stats.get("blkio_stats", {}).get("io_service_bytes_recursive", []) or []
            ):
                if entry.get("op") == "read":
                    read_bytes += entry.get("value", 0)
                elif entry.get("op") == "write":
                    write_bytes += entry.get("value", 0)

            # CPU percentage
            cpu_stats = sdk_stats.get("cpu_stats", {})
            precpu_stats = sdk_stats.get("precpu_stats", {})

            cpu_delta = cpu_stats.get("cpu_usage", {}).get("total_usage", 0) - precpu_stats.get(
                "cpu_usage", {}
            ).get("total_usage", 0)

            system_delta = cpu_stats.get("system_cpu_usage", 0) - precpu_stats.get(
                "system_cpu_usage", 0
            )

            online_cpus = cpu_stats.get("online_cpus", 1)
            cpu_percent = (
                (cpu_delta / system_delta * 100.0 * online_cpus) if system_delta > 0 else 0.0
            )

            # Memory (usage, limit) bytes
            memory_stats = sdk_stats.get("memory_stats", {})
            mem_usage = memory_stats.get("usage", 0)
            mem_limit = memory_stats.get("limit", 1)  # Prevent division by zero
            mem_inactive = memory_stats.get("stats", {}).get("inactive_file", 0)
            used_memory = max(0, mem_usage - mem_inactive)
            mem_percent = (used_memory / mem_limit * 100.0) if mem_limit else 0.0

            # Network IO
            net_rx = 0
            net_tx = 0
            for iface in sdk_stats.get("networks", {}).values():
                net_rx += iface.get("rx_bytes", 0)
                net_tx += iface.get("tx_bytes", 0)

            # Container ID
            container_id = sdk_stats.get("id", "")[:12]
            name = sdk_stats.get("name", "").lstrip("/")

            return DockerContainerStats(
                Container=container_id,
                ID=container_id,
                Name=name,
                BlockIO=(read_bytes, write_bytes),
                CPUPerc=round(cpu_percent, 2),
                MemPerc=round(mem_percent, 2),
                MemUsage=(used_memory, mem_limit),
                NetIO=(net_rx, net_tx),
                PIDs=sdk_stats.get("pids_stats", {}).get("current", 0),
                SDKStats=sdk_stats,  # keep the raw stats for more detailed information
            )
        except NotFound:
            raise NoSuchContainer(container_name)
        except APIError as e:
            raise ContainerException() from e