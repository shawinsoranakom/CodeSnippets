def init_limited_capi(self) -> None:
        self.limited_capi = self.codegen.limited_capi
        if self.limited_capi and (
                (self.varpos and self.pos_only < len(self.parameters)) or
                (any(p.is_optional() for p in self.parameters) and
                 any(p.is_keyword_only() and not p.is_optional() for p in self.parameters)) or
                any(c.broken_limited_capi for c in self.converters)):
            warn(f"Function {self.func.full_name} cannot use limited C API")
            self.limited_capi = False