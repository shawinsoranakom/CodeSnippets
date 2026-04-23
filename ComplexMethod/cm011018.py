def _normalize_backend_override(
        backend_override: dict[
            int | str,
            str | C10dBackend.Options | tuple[str, C10dBackend.Options],
        ],
        ndim: int,
        mesh_dim_names: tuple[str, ...] | None = None,
    ) -> Iterator[BackendConfig]:
        if mesh_dim_names is None:
            mesh_dim_names = ()
        for dim_idx, dim_name in zip_longest(range(ndim), mesh_dim_names):
            if dim_name is not None and dim_name in backend_override:
                if dim_idx in backend_override:
                    raise RuntimeError(
                        f"Found redundant dim index {dim_idx} and "
                        f"name {dim_name} in backend_override"
                    )
                val = backend_override.pop(dim_name)
            elif dim_idx in backend_override:
                val = backend_override.pop(dim_idx)
            else:
                yield (None, None)
                continue

            if isinstance(val, str):
                yield (val, None)
            elif isinstance(val, C10dBackend.Options):
                yield (None, val)
            else:
                yield val

        if backend_override:
            raise RuntimeError(
                f"Found invalid keys in backend_override: got {list(backend_override.keys())}, "
                f"expected integers in range [0, {ndim}) or one of {mesh_dim_names}"
            )