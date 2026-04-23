def check_hash_mismatches(
        logs1: list, logs2: list, compare_inputs: bool = False
    ) -> list[dict]:
        """
        Compares tensor hashes between two DebugMode runs, for checking run-to-run numerical divergence.

        This first validates the two log sequences have identical structure (same operations, input shapes/dtypes, etc.),
        then compares tensor hash values, and returns a list of call outputs where mismatches were found.
        Expects input logs to have been run with log_tensor_hashes, and looks for hashes in .log["hash"] & .log["input_hash"]
        (or .post_hashes & .pre_hashes for triton kernels).

        note: skips checking log pairs where hashes aren't present, but will raise if present in one & not the other.

        Args:
            logs1: logs from the first DebugMode run (from debug_mode.logs)
            logs2: logs from the second DebugMode run
            compare_inputs: If True, also compare input tensor hashes (default: only output checking)

        Returns:
            List of dictionaries describing hash mismatches. Each dict contains:
                - call_type: "torch op" or "triton kernel"
                - call: Operator/kernel name
                - arg_name: For triton kernels, the argument name; None for torch ops
                - pytree_path: For torch ops, the pytree path to the differing tensor; None for kernels
                - hash1: Hash value from the first run
                - hash2: Hash value from the second run
                - rel_diff: Relative difference between hash values
                - is_input_hash: True if this is an input hash, False for output hash

        Raises:
            ValueError: If logs have different lengths, call types, operator names, or call depths

        Usage::

            # Run model first time
            with DebugMode() as debug_mode, DebugMode.log_tensor_hashes():
                model(x)
                logs1 = debug_mode.logs

            # Run again, in exactly the same way
            with DebugMode() as debug_mode, DebugMode.log_tensor_hashes():
                model(x)
                logs2 = debug_mode.logs

            mismatches = DebugMode.check_hash_mismatches(logs1, logs2)
            for m in mismatches:
                print(f"{m['call']}: hash diff {m['rel_diff']:.2e}")
        """
        if len(logs1) != len(logs2):
            raise ValueError(f"Log lengths don't match: {len(logs1)} vs {len(logs2)}")

        difference_info = []
        for i, (log1, log2) in enumerate(zip(logs1, logs2)):
            # check call type
            call1_type = type(log1).__name__
            call2_type = type(log2).__name__
            if call1_type != call2_type:
                raise ValueError(
                    f"Call types don't match at index {i}: {call1_type} vs {call2_type}"
                )
            call_type = call1_type

            # check call name
            op1_name, op2_name = _get_call_name(log1), _get_call_name(log2)
            if op1_name != op2_name:
                raise ValueError(
                    f"Operators don't match at index {i}: {call_type}[{op1_name}] vs {call_type}[{op2_name}]"
                )
            op_name = op1_name

            # check call depth
            if log1.call_depth != log2.call_depth:
                raise ValueError(
                    f"Call depths for {call_type}[{op_name}] don't match at index {i}: {log1.call_depth} vs {log2.call_depth}"
                )

            # Redistribute: call args should be the same
            if isinstance(log1, _RedistributeCall):
                if tuple(log1) != tuple(log2):
                    raise ValueError(
                        f"Redistribute calls don't match at index {i}: {log1} vs {log2}"
                    )

            # Triton kernel: same arg names, arg types
            elif isinstance(log1, _TritonKernelCall):
                if log1.kwargs_str != log2.kwargs_str:
                    raise ValueError(
                        f"Triton kernel call args don't match for {log1.kernel_name} at index {i}:"
                        f"\n\nlog1: {log1.kwargs_str}\n\nlog2: {log2.kwargs_str}"
                    )

                def compare_triton_hashes(hashes1, hashes2, is_input):
                    if set(hashes1.keys()) != set(hashes2.keys()):  # type: ignore[union-attr]
                        raise AssertionError(
                            f"hash key mismatch: {set(hashes1.keys())} vs {set(hashes2.keys())}"
                        )
                    for key in hashes1:
                        if hashes1[key] != hashes2[key]:
                            difference_info.append(
                                {
                                    "call_type": "triton kernel",
                                    "call": op_name,
                                    "arg_name": key,
                                    "pytree_path": None,
                                    "hash1": hashes1[key],
                                    "hash2": hashes2[key],
                                    "rel_diff": _compute_rel_diff(
                                        hashes1[key], hashes2[key]
                                    ),
                                    "is_input_hash": is_input,
                                }
                            )

                # check output hashes
                has_post_1, has_post_2 = (
                    log1.post_hashes is not None,
                    log2.post_hashes is not None,
                )
                if has_post_1 != has_post_2:
                    raise ValueError(
                        f"Triton kernel post-hash presence inconsistent for {log1.kernel_name} "
                        f"at index {i}: log1 has post_hashes={has_post_1}, log2 has post_hashes={has_post_2}"
                    )

                if has_post_1:
                    compare_triton_hashes(
                        log1.post_hashes, log2.post_hashes, is_input=False
                    )

                # maybe check input hashes
                if compare_inputs:
                    has_pre_1, has_pre_2 = (
                        log1.pre_hashes is not None,
                        log2.pre_hashes is not None,
                    )
                    if has_pre_1 != has_pre_2:
                        raise ValueError(
                            f"Triton kernel pre-hash presence inconsistent for {log1.kernel_name} "
                            f"at index {i}: log1 has pre_hashes={has_pre_1}, log2 has pre_hashes={has_pre_2}"
                        )

                    if has_pre_1:
                        compare_triton_hashes(
                            log1.pre_hashes, log2.pre_hashes, is_input=True
                        )

            # regular log calls
            elif isinstance(log1, _OpCall):

                def compare_op_hashes(hashes1, hashes2, is_input):
                    def _helper(keypath, hash1, hash2):
                        if hash1 != hash2:
                            difference_info.append(
                                {
                                    "call_type": "torch op",
                                    "call": op_name,
                                    "arg_name": None,
                                    "pytree_path": keystr(keypath),
                                    "hash1": hash1,
                                    "hash2": hash2,
                                    "rel_diff": _compute_rel_diff(hash1, hash2),
                                    "is_input_hash": is_input,
                                }
                            )

                    tree_map_with_path(_helper, hashes1, hashes2)

                # check output hashes
                has_hash1 = log1.log is not None and "hash" in log1.log
                has_hash2 = log2.log is not None and "hash" in log2.log
                if has_hash1 != has_hash2:
                    raise ValueError(
                        f"Output hash presence inconsistent for triton kernel {call_type}[{op_name}] "
                        f"at index {i}: log1 has hash={has_hash1}, log2 has hash={has_hash2}"
                    )

                if has_hash1:
                    compare_op_hashes(
                        log1.log["hash"],  # type: ignore[union-attr]
                        log2.log["hash"],
                        is_input=False,
                    )

                # maybe check input hashes
                if compare_inputs:
                    has_hash1 = log1.log is not None and "input_hash" in log1.log
                    has_hash2 = log2.log is not None and "input_hash" in log2.log
                    if has_hash1 != has_hash2:
                        raise ValueError(
                            f"Input hash presence inconsistent for triton kernel {call_type}[{op_name}] "
                            f"at index {i}: log1 has input_hash={has_hash1}, log2 has input_hash={has_hash2}"
                        )

                    if has_hash1:
                        compare_op_hashes(
                            log1.log["input_hash"],  # type: ignore[union-attr]
                            log2.log["input_hash"],
                            is_input=True,
                        )

        return difference_info