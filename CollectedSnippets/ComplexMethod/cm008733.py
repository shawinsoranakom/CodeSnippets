def validate_cache_spec(spec: PoTokenCacheSpec):
    return (
        isinstance(spec, PoTokenCacheSpec)
        and isinstance(spec.write_policy, CacheProviderWritePolicy)
        and isinstance(spec.default_ttl, int)
        and isinstance(spec.key_bindings, dict)
        and all(isinstance(k, str) for k in spec.key_bindings)
        and all(v is None or isinstance(v, str) for v in spec.key_bindings.values())
        and bool([v for v in spec.key_bindings.values() if v is not None])
    )