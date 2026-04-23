def find_nccl_include_paths() -> list[str] | None:
    """Return possible include paths containing `nccl.h`.

    Considers `VLLM_NCCL_INCLUDE_PATH` and the `nvidia-nccl-cuXX` package.
    """
    paths: list[str] = []
    inc = envs.VLLM_NCCL_INCLUDE_PATH
    if inc and os.path.isdir(inc):
        paths.append(inc)

    try:
        spec = importlib.util.find_spec("nvidia.nccl")
        if spec and (locs := getattr(spec, "submodule_search_locations", None)):
            for loc in locs:
                inc_dir = os.path.join(loc, "include")
                if os.path.exists(os.path.join(inc_dir, "nccl.h")):
                    paths.append(inc_dir)
    except Exception as e:
        logger.debug("Failed to find nccl include path from nvidia.nccl package: %s", e)

    seen: set[str] = set()
    out: list[str] = []
    for p in paths:
        if p and p not in seen:
            out.append(p)
            seen.add(p)
    return out or None