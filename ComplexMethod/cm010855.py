def pre_compile(
        self,
        flat_fn: TraceFn,
        flat_args: list[FxValue],
        flat_args_descs: list[AOTInput],
        aot_config: AOTConfig,
        *,
        fw_metadata: ViewAndMutationMeta,
    ) -> tuple[TraceFn, list[FxValue], list[AOTInput], ViewAndMutationMeta]:
        # Use information about whether or not flat_fn mutates its arguments
        # or not to handle dupe args

        # Strategy 1: For any input that is not mutated, we can leafify it if we
        # need to remove a duplicate.
        leaf_flat_args: list[FxValue] = []
        leaf_flat_args_descs: list[AOTInput] = []
        args_set = set()
        ok = True

        for i, (a, a_desc) in enumerate(zip(flat_args, flat_args_descs)):
            if not isinstance(a, torch.Tensor):
                leaf_flat_args.append(a)
                leaf_flat_args_descs.append(a_desc)
            elif a not in args_set:
                args_set.add(a)
                leaf_flat_args.append(a)
                leaf_flat_args_descs.append(a_desc)
            elif (
                not fw_metadata.input_info[i].mutates_data
                and not fw_metadata.input_info[i].mutates_metadata
            ):
                leaf_flat_args.append(a.detach().requires_grad_(a.requires_grad))
                leaf_flat_args_descs.append(a_desc)
            else:
                ok = False
                break

        if ok:
            self.needs_post_compile = False
            return flat_fn, leaf_flat_args, leaf_flat_args_descs, fw_metadata

        if requires_subclass_dispatch(leaf_flat_args, fw_metadata):  # type: ignore[arg-type]
            raise RuntimeError(
                """\
        Encountered duplicate inputs that are mutated in the graph, but at least one input/output
        to the graph is a tensor subclass. This is not supported today. You can try to
        remove the aliasing yourself as a workaround, or otherwise file an issue on github."""
            )

        # export path: ban duplicate inputs for now, add later if requested.
        if aot_config.is_export:
            raise RuntimeError(
                f"""\
        Encountered duplicated inputs that are mutated in the graph you are trying to export.
        This functionality is currently not supported. If needed, please file a github issue.

        fw_metadata={str(fw_metadata)}
            """
            )

        # Strategy 2: Duplicate specialization
        #
        # When we have duplicate arguments in a function call, we need to handle them specially.
        # For example, if we have a function call f(a, b, a, c), we need to:
        #
        # 1. Remove duplicates to get a deduplicated list [a, b, c]
        # 2. Compile our function to work with this deduplicated list
        # 3. At runtime, convert incoming arguments with duplicates to the deduplicated form
        # 4. Pass the deduplicated arguments to our compiled function
        #
        # To do this, we need two helper functions:
        #
        # - remove_dupe_args: Converts [a, b, a, c] -> [a, b, c]
        # - add_dupe_args: Converts [a, b, c] -> [a, b, a, c]
        #
        # For our example [a, b, a, c], we track:
        #
        # - seen_args = {a: 0, b: 1, c: 2} (maps each unique arg to its first position)
        # - add_dupe_map = [0, 1, 0, 2] (tells us how to reconstruct the original list)
        # - keep_arg_mask = [True, True, False, True] (tells us which args to keep when deduplicating)

        seen_args: dict[Tensor, int] = {}
        # Implicitly map duped arg position (list index) to de-duped arg position
        keep_arg_mask: list[bool] = []
        add_dupe_map: list[int] = []
        duped_arg_len = len(flat_args)

        j = 0  # index into deduped_flat_args
        for t in flat_args:
            if isinstance(t, torch.Tensor):
                if t in seen_args:
                    keep_arg_mask.append(False)
                    add_dupe_map.append(seen_args[t])
                    continue
                seen_args[t] = j

            keep_arg_mask.append(True)
            add_dupe_map.append(j)
            j += 1
        if len(add_dupe_map) != duped_arg_len:
            raise AssertionError(
                f"Expects add_dupe_map to have length {duped_arg_len} but got {len(add_dupe_map)}"
            )

        self.keep_arg_mask = keep_arg_mask
        self.add_dupe_map = add_dupe_map

        deduped_flat_args = self.remove_dupe_args(flat_args)
        # TODO: instead of arbitrarily removing args, it might be useful to
        # have a record that these were duped, perhaps as a mutable attribute
        # on the kept arg?  Do this if someone needs it
        deduped_flat_args_descs = self.remove_dupe_args(flat_args_descs)

        # Update our input metadata to remove duped input metadata.
        updated_fw_metadata = remove_dupe_metadata(
            fw_metadata, keep_arg_mask, add_dupe_map
        )

        if (
            tracing_context := TracingContext.try_get()
            and aot_config.aot_autograd_arg_pos_to_source
        ):
            # TODO(voz): This structure is 1:1, we could consider an alternate structure like
            # kept_pos:[dupe_arg_pos], however, add_dupe_map is 1:1 so we would need a new structure there,
            # which feels like needless complexity for a tiny bit of efficiency at this point.
            for dupe_arg_pos, (kept_pos, keep_arg) in enumerate(
                zip(add_dupe_map, keep_arg_mask)
            ):
                if not keep_arg:
                    dupe_arg_source = aot_config.aot_autograd_arg_pos_to_source[
                        dupe_arg_pos
                    ]
                    kept_arg_source = aot_config.aot_autograd_arg_pos_to_source[
                        kept_pos
                    ]
                    tracing_context.guards_context.aotautograd_guards.append(  # type: ignore[attr-defined]
                        DuplicateInputs(kept_arg_source, dupe_arg_source)
                    )

        @simple_wraps(flat_fn)
        def wrapped_flat_fn(
            *args: FxValue,
        ) -> tuple[list[FxValue], list[AOTOutput]]:
            outs, out_descs = call_and_expect_output_descs(
                flat_fn,
                self.add_dupe_args(args),  # type: ignore[arg-type]
            )
            return outs, out_descs

        if config.debug_assert:
            ref_fw_metadata = run_functionalized_fw_and_collect_metadata(
                without_output_descs(wrapped_flat_fn),
                flat_args_descs=deduped_flat_args_descs,
                static_input_indices=aot_config.static_input_indices,
                keep_input_mutations=fw_metadata.keep_input_mutations,
            )(*deduped_flat_args)
            if ref_fw_metadata != updated_fw_metadata:
                raise AssertionError(
                    f"ref_metadata={str(ref_fw_metadata)}, actual_metadata={str(updated_fw_metadata)}"
                )

        return (
            wrapped_flat_fn,
            deduped_flat_args,
            deduped_flat_args_descs,
            updated_fw_metadata,
        )