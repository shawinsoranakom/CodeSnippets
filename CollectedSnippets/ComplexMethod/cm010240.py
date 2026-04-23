def step_meta_parameter(name, value, direction, meta, m=m, n=n, k=k, bm=bm, bk=bk):
        # return next value in positive or negative direction, or
        # input value if the step will result an invalid
        # value. The input value is assumed to be valid.

        is_log = name in {"SPLIT_N", "TILE_M", "TILE_N", "num_warps"}
        min_value = dict(
            SPLIT_N=1, TILE_M=16, TILE_N=16, num_warps=1, num_stages=1, GROUP_SIZE=1
        )[name]
        max_value = dict(
            SPLIT_N=n // meta["TILE_N"], TILE_M=bm, TILE_N=n // meta["SPLIT_N"]
        ).get(name)
        value_step = dict(
            SPLIT_N=2, TILE_M=2, TILE_N=2, num_warps=2, num_stages=1, GROUP_SIZE=1
        )[name]
        if is_log:
            next_value = (
                value * value_step**direction
                if direction > 0
                else value // (value_step ** abs(direction))
            )
        else:
            next_value = value + value_step * direction
        if min_value is not None:
            next_value = max(next_value, min_value)
        if max_value is not None:
            next_value = min(next_value, max_value)
        if name == "SPLIT_N" and n % next_value != 0:
            return value
        # Hard-skip parameter combinations that break CUDA state for pytorch:
        if (dtype, name, next_value, m, n, k, bm, bk) in {
            (torch.float32, "num_warps", 32, 256, 256, 256, 16, 16),
            (torch.float32, "num_warps", 16, 256, 256, 256, 32, 32),
            (torch.float32, "num_warps", 16, 256, 256, 256, 64, 64),
            (torch.float32, "num_warps", 16, 256, 256, 256, 128, 128),
            (torch.float32, "num_warps", 16, 512, 512, 256, 128, 128),
        } and re.match(r"NVIDIA A100[^\d]", device_name) is not None:
            return value
        return next_value