def bisect_cmd_args(self) -> list[str]:
        args = []
        if self.fail_fast:
            args.append("--failfast")
        if self.fail_env_changed:
            args.append("--fail-env-changed")
        if self.timeout:
            args.append(f"--timeout={self.timeout}")
        if self.hunt_refleak is not None:
            args.extend(self.hunt_refleak.bisect_cmd_args())
        if self.test_dir:
            args.extend(("--testdir", self.test_dir))
        if self.memory_limit:
            args.extend(("--memlimit", self.memory_limit))
        if self.gc_threshold:
            args.append(f"--threshold={self.gc_threshold}")
        if self.use_resources:
            simple = ','.join(resource
                              for resource, value in self.use_resources.items()
                              if value is None)
            if simple:
                args.extend(("-u", simple))
            for resource, value in self.use_resources.items():
                if value is not None:
                    args.extend(("-u", f"{resource}={value}"))
        if self.python_cmd:
            cmd = shlex.join(self.python_cmd)
            args.extend(("--python", cmd))
        if self.randomize:
            args.append(f"--randomize")
        if self.parallel_threads:
            args.append(f"--parallel-threads={self.parallel_threads}")
        args.append(f"--randseed={self.random_seed}")
        return args