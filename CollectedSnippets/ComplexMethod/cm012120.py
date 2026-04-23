def get_bisect_range(
        cls, backend_name: str, subsystem_name: str
    ) -> tuple[int, int]:
        file_path = os.path.join(
            cls.get_dir(), backend_name, f"{subsystem_name}_bisect_range.txt"
        )
        lines = cls.read_lines_from_file(file_path)
        low = None
        high = None
        # pyrefly: ignore [bad-assignment]
        for line in reversed(lines):
            if line.startswith("low="):
                low = int(line.strip().split("=")[1])
            elif line.startswith("high="):
                high = int(line.strip().split("=")[1])

            if low is not None and high is not None:
                break

        if low is None or high is None:
            raise RuntimeError(
                f"Trying to get bisect range when it is not set: subsystem {subsystem_name}"
            )

        return low, high