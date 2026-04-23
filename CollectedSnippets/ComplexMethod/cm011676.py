def from_env_var(cls, env_var: str) -> Self:
        """
        Create an in-memory cache from an environment variable.
        Args:
            env_var (str): Name of the environment variable containing cache data.
        Returns:
            InMemoryCache: An instance populated from the environment variable.
        Raises:
            CacheError: If the environment variable is malformed or contains invalid data.
        """
        cache = cls()

        if (env_val := getenv(env_var)) is None:
            # env_var doesn't exist = empty cache
            return cache

        for kv_pair in env_val.split(";"):
            # ignore whitespace prefix/suffix
            kv_pair = kv_pair.strip()

            if not kv_pair:
                # kv_pair could be '' if env_val is '' or has ; suffix
                continue

            try:
                # keys and values should be comma separated
                key_bytes_repr, value_bytes_repr = kv_pair.split(",", 1)
            except ValueError as err:
                raise CacheError(
                    f"Malformed kv_pair {kv_pair!r} from env_var {env_var!r}, likely missing comma separator."
                ) from err

            # ignore whitespace prefix/suffix, again
            key_bytes_repr, value_bytes_repr = (
                key_bytes_repr.strip(),
                value_bytes_repr.strip(),
            )

            try:
                # check that key_bytes_str is an actual, legitimate encoding
                key_bytes = literal_eval(key_bytes_repr)
            except (ValueError, SyntaxError) as err:
                raise CacheError(
                    f"Malformed key_bytes_repr {key_bytes_repr!r} in kv_pair {kv_pair!r}, encoding is invalid."
                ) from err
            try:
                # check that value_bytes_str is an actual, legitimate encoding
                value_bytes = literal_eval(value_bytes_repr)
            except (ValueError, SyntaxError) as err:
                raise CacheError(
                    f"Malformed value_bytes_repr {value_bytes_repr!r} in kv_pair {kv_pair!r}, encoding is invalid."
                ) from err

            try:
                key = pickle.loads(key_bytes)
            except pickle.UnpicklingError as err:
                raise CacheError(
                    f"Malformed key_bytes_repr {key_bytes_repr!r} in kv_pair {kv_pair!r}, not un-pickle-able."
                ) from err
            try:
                value = pickle.loads(value_bytes)
            except pickle.UnpicklingError as err:
                raise CacheError(
                    f"Malformed value_bytes_repr {value_bytes_repr!r} in kv_pair {kv_pair!r}, not un-pickle-able."
                ) from err

            # true duplicates, i.e. multiple occurrences of the same key => value
            # mapping are ok and treated as a no-op; key duplicates with differing
            # values, i.e. key => value_1 and key => value_2 where value_1 != value_2,
            # are not okay since we don't allow overwriting cached values (it's bad regardless)
            if (not cache.insert(key, value)) and (cache.get(key) != value):
                raise CacheError(
                    f"Multiple values for key {key!r} found, got {cache.get(key)!r} and {value!r}."
                )

        return cache