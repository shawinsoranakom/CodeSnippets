def get_template_configs(
        self,
        kernel_inputs: KernelInputs,
        templates: list[KernelTemplate | ExternKernelChoice],
        op_name: str,
        kwarg_overrides: dict[str, dict[str, Any]] | None = None,
    ) -> list[ChoiceCaller]:
        """
        Get list of ChoiceCallers for MM templates using template-specific heuristics.

        Args:
            kernel_inputs: MMKernelInputs containing input tensor nodes and matrix indices
            layout: Output layout
            templates: List of template objects (KernelTemplate or ExternKernelChoice)
            op_name: Operation name (e.g., "bmm", "baddbmm", "addmm", "mm_plus_mm")
            kwarg_overrides: Optional dict of kwargs to override for each template heuristic,
                             indexed by template.uid. These only override the per config kwargs, not the extra kwargs
        Returns:
            List of ChoiceCaller objects from the templates
        """
        if kwarg_overrides is None:
            kwarg_overrides = {}
        input_tensors = kernel_inputs.nodes()
        if len(input_tensors) < 2:
            raise ValueError(f"Need at least 2 input tensors, got {len(input_tensors)}")
        layout = kernel_inputs.output_layout()
        # First pass: Create dict of template.uid to generator of KernelTemplateChoice objects
        template_choices = {}
        for template in templates:
            template_choices[template.uid] = self.get_ktc(
                kernel_inputs,
                template,
                op_name,
                kwarg_overrides.get(template.uid, {}),
            )

        # Second pass: Adjust the template choices
        adjusted_choices = self._finalize_template_configs(
            template_choices,
            kernel_inputs,
            templates,
            op_name,
            kwarg_overrides,
        )
        # Layout optimization: if all choices are ExternKernelChoice and layout is FixedLayout, convert to FlexibleLayout
        if self._need_to_fix_layout(adjusted_choices, op_name):
            layout = kernel_inputs.output_layout(flexible=False)
            for ktc in adjusted_choices:
                ktc.layout = layout
                # for good measure, delete the cached ChoiceCaller from the ktc if it existed.
                # ExternKernelChoice are cheap to generate
                if hasattr(ktc, "_choice"):
                    del ktc._choice
        # Third pass: Convert to ChoiceCaller objects
        return [ktc.choice for ktc in adjusted_choices if ktc.choice is not None]