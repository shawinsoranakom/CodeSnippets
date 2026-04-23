def _scrubbed_inductor_config_for_logging() -> str | None:
    """
    Method to parse and scrub uninteresting configs from inductor config
    """

    # TypeSafeSerializer for json.dumps()
    # Skips complex types as values in config dict
    class TypeSafeSerializer(json.JSONEncoder):
        def default(self, o: Any) -> Any:
            try:
                return super().default(o)
            except Exception:
                return "Value is not JSON serializable"

    keys_to_scrub: set[Any] = set()
    inductor_conf_str = None
    inductor_config_copy = None

    if torch._inductor.config:
        try:
            inductor_config_copy = torch._inductor.config.get_config_copy()
        except (TypeError, AttributeError, RuntimeError, AssertionError):
            inductor_conf_str = "Inductor Config cannot be pickled"

    if inductor_config_copy is not None:
        try:
            for key, val in inductor_config_copy.items():
                if not isinstance(key, str):
                    keys_to_scrub.add(key)
                # Convert set() to list for json.dumps()
                if isinstance(val, set):
                    inductor_config_copy[key] = list(val)
            # Evict unwanted keys
            for key in keys_to_scrub:
                del inductor_config_copy[key]
            # Stringify Inductor config
            inductor_conf_str = json.dumps(
                inductor_config_copy,
                cls=TypeSafeSerializer,
                skipkeys=True,
                sort_keys=True,
            )
        except Exception:
            # Don't crash because of runtime logging errors
            inductor_conf_str = "Inductor Config is not JSON serializable"
    return inductor_conf_str