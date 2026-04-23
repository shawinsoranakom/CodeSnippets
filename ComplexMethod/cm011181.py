def __torch_dispatch__(  # type: ignore[no-untyped-def]
        self, func, types, args=..., kwargs=None
    ):
        # 1. Get the runtime estimate
        out, op_time = self._estimate_runtime(func, args, kwargs)
        flat_outs, _ = tree_flatten(out)
        out_storages_cuda: set[UntypedStorage] = set()
        out_storages_cpu: set[UntypedStorage] = set()
        cuda_devices: set[torch.device] = set()
        for o in flat_outs:
            if isinstance(o, torch.Tensor):
                if o.device.type == "cuda":
                    out_storages_cuda.update(get_untyped_storages(o))
                    cuda_devices.add(o.device)
                else:
                    out_storages_cpu.update(get_untyped_storages(o))

        # Check if there's more than 1 CUDA device
        if len(cuda_devices) > 1:
            raise AssertionError(
                f"{func.__name__}'s output has more than 1 CUDA devices {cuda_devices}"
            )

        # 2. Get the memory consumed by output
        nbytes_cuda = sum(
            math.ceil(st.nbytes() / _PYTORCH_MIN_ALLOCATE) * _PYTORCH_MIN_ALLOCATE
            for st in out_storages_cuda
        )
        nbytes_cpu = sum(st.nbytes() for st in out_storages_cpu)
        nbytes = nbytes_cuda + nbytes_cpu
        # 3. Get the current operator index, output storage identifiers and inplace metadata
        out_storages = out_storages_cuda | out_storages_cpu
        curr_idx, output_ids, mod_inplace_info = self._get_inplace_metadata(
            func, out_storages
        )
        # 4. Determine if the function is in-place, random-op or a view-like
        is_view_like = is_view_fn(func) or is_inplace_view_fn(func)
        is_rand_op = torch.Tag.nondeterministic_seeded in func.tags
        if is_view_like:
            nbytes = 0
        # sdpa has non-deterministic seed, but might be deterministic
        # if no dropout is applied
        if func.overloadpacket.__name__ == "_scaled_dot_product_flash_attention":
            # pyrefly: ignore [missing-attribute]
            is_rand_op = kwargs.get("dropout_p", 0) != 0
        # 5. Create metadata information per active non-leaf module
        for mod_fqn in self._mod_tracker.parents:
            if mod_fqn in self._leaf_modules:
                continue
            acm = _SACMetadata(
                func=func,
                time_taken=op_time,
                memory_used=nbytes,
                curr_idx=curr_idx,
                output_ids=output_ids,
                inplace_info=mod_inplace_info[mod_fqn],
                is_view_like=is_view_like,
                is_rand_op=is_rand_op,
            )
            if acm_stats := self._sac_mod_metadata.get(mod_fqn, None):
                acm_stats.sac_metadata.append(acm)
            else:
                if mod_fqn != "Global":
                    raise AssertionError(f"Module {mod_fqn} not found in AC Mod Stats")
                self._sac_metadata.append(acm)

        return out