def _load_tasks(self) -> None:
        """Load tasks from the repository data files."""
        if self._repo_path is None:
            return

        data_dir = self._repo_path / "data"

        if not data_dir.exists():
            # Try alternative locations
            for alt_path in ["thudm_data", "tasks", "benchmarks"]:
                alt_dir = self._repo_path / alt_path
                if alt_dir.exists():
                    data_dir = alt_dir
                    break

        # Load tasks for each environment
        for env_name in self.ENVIRONMENTS:
            env_dir = data_dir / env_name
            if not env_dir.exists():
                continue

            self._tasks[env_name] = []

            # Try JSON file first
            tasks_file = env_dir / f"{self.split}.json"
            if not tasks_file.exists():
                tasks_file = env_dir / "tasks.json"

            if tasks_file.exists():
                with open(tasks_file) as f:
                    self._tasks[env_name] = json.load(f)
                continue

            # Try JSONL file (AgentBench format)
            jsonl_file = env_dir / f"{self.split}.jsonl"
            if not jsonl_file.exists():
                jsonl_file = env_dir / "standard.jsonl"

            if jsonl_file.exists():
                with open(jsonl_file) as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            self._tasks[env_name].append(json.loads(line))
                continue

            # Try to load from individual task files
            for task_file in env_dir.glob("*.json"):
                if task_file.stem not in ("config", "metadata"):
                    with open(task_file) as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            self._tasks[env_name].extend(data)
                        else:
                            self._tasks[env_name].append(data)