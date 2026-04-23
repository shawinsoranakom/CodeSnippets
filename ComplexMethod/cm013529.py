def _render_range_for_constraint_violation(
        self, source: Source, c: StrictMinMaxConstraint | RelaxedUnspecConstraint
    ) -> str:
        if isinstance(c, StrictMinMaxConstraint):
            lower, upper = c.vr.lower, c.vr.upper
            default = self._default_value_range()
            if lower <= default.lower:
                lower = None
            if upper >= default.upper:
                upper = None
            c_render = (
                f"{self._debug_name(source)} = {source.name} in the specified range"
            )
            if lower is not None and upper is not None:
                c_render += f" {lower} <= {self._debug_name(source)} <= {upper}"
            elif lower is None and upper is not None:
                c_render += f" {self._debug_name(source)} <= {upper}"
            elif lower is not None and upper is None:
                c_render += f" {lower} <= {self._debug_name(source)}"
            return c_render
        return c.render(source)