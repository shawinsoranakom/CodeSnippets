def normalize_value(x):
    """Return a stable, JSON-serializable canonical form for hashing.
    Order: primitives, special types (Enum, callable, torch.dtype, Path), then
    generic containers (Mapping/Set/Sequence) with recursion.
    """
    # Fast path
    if x is None or isinstance(x, (bool, int, float, str)):
        return x

    # Enums: tag with FQN to avoid primitive collisions.
    # Ex: Enum(1) vs int(1) -> ("module.QualName", value).
    if isinstance(x, enum.Enum):
        enum_type = f"{x.__class__.__module__}.{x.__class__.__qualname__}"
        return (enum_type, normalize_value(x.value))

    # Classes (types) are accepted and canonicalized by their fully-qualified
    # name (module.qualname) for a stable identifier.
    # Instances are only accepted if they expose uuid(); otherwise they are
    # rejected to avoid under-hashing object state.

    # Callables: accept classes only; reject funcs/lambdas/methods.
    # Used by LogitsProcessor types and ModelConfig.hf_overrides.
    if isinstance(x, type):
        module = getattr(x, "__module__", "")
        qual = getattr(x, "__qualname__", getattr(x, "__name__", ""))
        return ".".join([p for p in (module, qual) if p]) or repr(x)

    # Prefer stable uuid identifiers for objects that provide them, even if
    # they are callable instances (e.g., InductorPass wrappers).
    if hasattr(x, "uuid") and callable(getattr(x, "uuid", None)):
        return x.uuid()

    if callable(x):
        raise TypeError("normalize_value: function or callable instance unsupported")

    # Torch dtype: stringify (torch.float64 -> "torch.float64").
    # We rely on the string form here; dtype-bearing fields that need additional
    # disambiguation should encode that at the config layer.
    if isinstance(x, torch.dtype):
        return str(x)

    # Bytes
    if isinstance(x, (bytes, bytearray)):
        return x.hex()

    # Paths (canonicalize)
    if isinstance(x, pathlib.Path):
        try:
            return str(x.expanduser().resolve())
        except Exception:
            return str(x)

    # Dataclasses: represent as (FQN, sorted(field,value) tuple) for stability.
    if is_dataclass(x):
        type_fqn = f"{x.__class__.__module__}.{x.__class__.__qualname__}"
        items = tuple(
            (f.name, normalize_value(getattr(x, f.name)))
            for f in sorted(fields(x), key=lambda f: f.name)
        )
        return (type_fqn, items)

    # Containers (generic)
    if isinstance(x, Mapping):
        return tuple(sorted((str(k), normalize_value(v)) for k, v in x.items()))
    if isinstance(x, Set):
        return tuple(sorted(repr(normalize_value(v)) for v in x))
    if isinstance(x, Sequence) and not isinstance(x, (str, bytes, bytearray)):
        return tuple(normalize_value(v) for v in x)

    # PretrainedConfig
    if hasattr(x, "to_json_string") and callable(x.to_json_string):
        try:
            return x.to_json_string()
        except (TypeError, ValueError):
            # to_json_string() may fail for trust-remote-code configs
            # with non-JSON-serializable nested objects. Fall back to
            # normalizing the dict representation recursively.
            if hasattr(x, "to_dict") and callable(x.to_dict):
                return normalize_value(x.to_dict())
            raise

    # Unsupported type: e.g., modules, generators, open files, or objects
    # without a stable JSON/UUID representation. Hard-error to avoid
    # under-hashing.
    # If you hit this, either reshape your config to use supported primitives
    # and containers, or extend normalize_value to provide a stable encoding
    # (e.g., via uuid() or to_json_string()) for this type.
    raise TypeError(
        f"normalize_value: unsupported type '{type(x).__name__}'. "
        "Ensure config values use supported primitives/containers or add a "
        "stable representation for this type."
    )