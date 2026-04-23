def _validate_numa_bind_cpus(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        if not value:
            raise ValueError("numa_bind_cpus must not be empty.")

        for cpuset in value:
            if not cpuset:
                raise ValueError("numa_bind_cpus entries must not be empty.")
            if not _NUMACTL_CPUSET_PATTERN.fullmatch(cpuset):
                raise ValueError(
                    "numa_bind_cpus entries must use numactl CPU list syntax, "
                    "for example '0-3' or '0,2,4-7'."
                )
            for part in cpuset.split(","):
                if "-" not in part:
                    continue
                start_str, end_str = part.split("-", 1)
                if int(start_str) > int(end_str):
                    raise ValueError(
                        f"numa_bind_cpus ranges must be ascending, but got '{cpuset}'."
                    )
        return value