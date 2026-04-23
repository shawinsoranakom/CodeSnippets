def _need_to_fix_layout(
        self,
        adjusted_choices: list[KernelTemplateChoice],
        op_name: str,
    ) -> bool:
        """
        Check if we need to fix the layout instead of keeping it flexible

        Args:
            ktc: KernelTemplateChoice object

        Returns:
            True if we need to fix the layout, False otherwise
        """
        # TODO: debug and fix
        # NOTE: on mps, we see issues with flexible layouts on baddmm. This check just makes sure
        # that for mps, everything stays as it was before this optimization
        if len(adjusted_choices) > 0:
            if adjusted_choices[0].inputs.device_type == "mps" and op_name not in [
                "mm",
                "addmm",
            ]:
                return True

        # Since the following backends are not using get_mm_configs yet through the singular call,
        if not (config.max_autotune or config.max_autotune_gemm):
            # no danger of using other backends than ATEN
            if not config.max_autotune_allow_flexible_layouts and op_name not in [
                # The historical implementation for mm and addmm allowed had flexible layouts in the
                # not max-autotune world
                "mm",
                "addmm",
            ]:
                # TODO: deprecate this by migrating users to the new behavior
                return True
            return False

        if not config.max_autotune_allow_flexible_layouts:
            # we always need to fix the layout
            return True

        # Since the following backends are not using get_template_configs yet through the singular call,
        # we don't know if they are a valid choice or not. Instead, just skip the optimization
        # defensively.
        # TODO(coconutruben): remove this once CPP,CK,CUTLASS are supported
        if _use_autotune_backend("CUTLASS"):
            return True
        if _use_autotune_backend("CK") or _use_autotune_backend("CKTILE"):
            return True
        if _use_autotune_backend("CPP"):
            return True
        return any(
            not isinstance(ktc.template, ExternKernelChoice) for ktc in adjusted_choices
        )