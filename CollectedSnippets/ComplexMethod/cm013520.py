def _rename_unbacked_to(self, orig_s: sympy.Symbol, new_s: sympy.Symbol) -> None:
        if not isinstance(orig_s, sympy.Symbol):
            raise AssertionError(f"Expected sympy.Symbol, got {orig_s}")
        if not isinstance(new_s, sympy.Symbol):
            raise AssertionError(f"Expected sympy.Symbol, got {new_s}")
        if not free_unbacked_symbols(new_s):
            raise AssertionError(
                f"Expected new_s to have free unbacked symbols: {new_s}"
            )
        if not free_unbacked_symbols(orig_s):
            raise AssertionError(
                f"Expected orig_s to have free unbacked symbols: {orig_s}"
            )
        dest = self.replacements.get(orig_s)
        if dest is not None:
            if free_unbacked_symbols(dest):
                raise AssertionError(f"{orig_s} -> {dest}")
        self._set_replacement(orig_s, new_s, "rename_unbacked_to")
        self.unbacked_renamings[orig_s] = new_s
        if dest is not None:
            self._set_replacement(new_s, dest, "rename_unbacked_to_dest")