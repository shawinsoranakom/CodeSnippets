def find_info(
        f: NativeFunction,
    ) -> tuple[dict[str, DifferentiabilityInfo] | None, bool]:
        # Don't bother matching info to generated out= variants
        if "generated" in f.tags and f.func.kind() == SchemaKind.out:
            return None, False

        # (1) Check for an exact match
        if f.func in differentiability_infos:
            return differentiability_infos[f.func], True

        # (2) If no exact match, check if the out-of-place variant
        # of this operator has a match.
        # i.e mul() for mul_() or mul_out()
        # note(crcrpar): Check foreach or not because in-place foreach functions use backward defined for the existing
        # native functions instead of the out-place counterparts.
        f_sig = f.func.signature(strip_default=True)
        if f_sig in functional_info_by_signature and not is_foreach_func(f):
            return functional_info_by_signature[f_sig], False

        # (3) Some operators have a derivative explicitly defined for the mutable
        # variant, but get a code-generated out-of-place variant which does *not*
        # come with a derivative formula.
        # For the generated out-of-place variant, use the mutable variant's formula
        # if it exists.
        if "generated" in f.tags and f_sig in non_functional_info_by_signature:
            info_dict = non_functional_info_by_signature[f_sig]
            # See https://github.com/pytorch/pytorch/pull/76320/files#r874816389
            if any(
                any("self" in str(input.nctype.name) for input in info.all_saved_inputs)
                for info in info_dict.values()
            ):
                raise AssertionError(
                    f"Attempted to convert a derivative formula for a mutable operator "
                    f'to be used automatically by its functional variant ("{str(f.func)}"). '
                    "This is not currently supported (we'd need to fix up the formula in the codegen)."
                )
            return info_dict, False

        # (4) Generate derivative information of foreach functions if none is defined in `derivatives.yaml`
        if is_foreach_func(f):
            if f.func in differentiability_infos:
                raise AssertionError(
                    f"Foreach function {f.func.name} already has differentiability info"
                )
            diff_info, is_generated = gen_foreach_derivativeinfo(
                f,
                functional_info_by_signature,
                non_functional_info_by_signature,
            )
            if diff_info is None:
                return None, False
            # TODO(crcrpar): Avoid hard coding "Default" ideally.
            diff_info_dict = {"Default": diff_info}
            if is_generated:
                differentiability_infos[f.func] = diff_info_dict
                functional_info_by_signature[f.func] = diff_info_dict
            return diff_info_dict, is_generated

        return None, False