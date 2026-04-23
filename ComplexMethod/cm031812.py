def why_not_viable(self) -> str | None:
        if self.name == "_SAVE_RETURN_OFFSET":
            return None  # Adjusts next_instr, but only in tier 1 code
        if "INSTRUMENTED" in self.name:
            return "is instrumented"
        if "replaced" in self.annotations:
            return "is replaced"
        if self.name in ("INTERPRETER_EXIT", "JUMP_BACKWARD"):
            return "has tier 1 control flow"
        if self.properties.needs_this:
            return "uses the 'this_instr' variable"
        if len([c for c in self.caches if c.name != "unused"]) > 2:
            return "has too many cache entries"
        if self.properties.error_with_pop and self.properties.error_without_pop:
            return "has both popping and not-popping errors"
        return None