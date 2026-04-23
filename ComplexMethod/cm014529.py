def write_sharded_with_template(
        self,
        filename: str | Path,
        template_fn: str | Path,
        items: Iterable[T],
        *,
        key_fn: Callable[[T], str],
        env_callable: Callable[[T], dict[str, list[str]]],
        num_shards: int,
        base_env: dict[str, Any] | None = None,
        sharded_keys: set[str],
    ) -> None:
        file = Path(filename)
        if file.is_absolute():
            raise AssertionError(f"filename must be relative: {filename}")
        everything: dict[str, Any] = {"shard_id": "Everything"}
        shards: list[dict[str, Any]] = [
            {"shard_id": f"_{i}"} for i in range(num_shards)
        ]
        all_shards = [everything] + shards

        if base_env is not None:
            for shard in all_shards:
                shard.update(base_env)

        for key in sharded_keys:
            for shard in all_shards:
                if key in shard:
                    if not isinstance(shard[key], list):
                        raise AssertionError("sharded keys in base_env must be a list")
                    shard[key] = shard[key].copy()
                else:
                    shard[key] = []

        def merge_env(into: dict[str, list[str]], from_: dict[str, list[str]]) -> None:
            for k, v in from_.items():
                if k not in sharded_keys:
                    raise AssertionError(f"undeclared sharded key {k}")
                into[k] += v

        if self.dry_run:
            # Dry runs don't write any templates, so incomplete environments are fine
            items = ()

        for item in items:
            key = key_fn(item)
            sid = string_stable_hash(key) % num_shards
            env = env_callable(item)

            merge_env(shards[sid], env)
            merge_env(everything, env)

        for shard in all_shards:
            shard_id = shard["shard_id"]
            self.write_with_template(
                file.with_stem(f"{file.stem}{shard_id}"),
                template_fn,
                lambda: shard,
            )

        # filenames is used to track compiled files, but FooEverything.cpp isn't meant to be compiled
        self.files.discard(self.install_dir / file.with_stem(f"{file.stem}Everything"))