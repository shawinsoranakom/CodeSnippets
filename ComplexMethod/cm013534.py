def _update_var_to_range(
        self,
        symbol: sympy.Symbol,
        vr: ValueRanges[sympy.Expr],
        vr_sloc: ValueRangesSLoc | None = None,
        *,
        is_constraint: bool = False,
    ) -> None:
        lower, upper = vr.lower, vr.upper

        # If we have a size-like unbacked SymInt, refuse to refine the range to be
        # less than two.  This is because when we intersect this range
        # with [2, inf] for size oblivious tests, the range would be
        # unsatisfiable.  In other words, once you have a size-like
        # unbacked SymInt, we can never learn that it is exactly zero or one,
        # because we would now give inconsistent results for all size
        # oblivous tests!
        if upper < 2 and symbol in self.size_like:
            vr = ValueRanges(lower, 2)

        # Updates the range and the guards corresponding to each bound of the symbol.
        if symbol not in self.var_to_range:
            self.log.debug("_update_var_to_range %s = %s (new)", symbol, vr)
            self.var_to_range[symbol] = vr
            if vr_sloc is None:
                sloc = self._get_sloc()
                vr_sloc = ValueRangesSLoc(sloc, sloc)
            self.var_to_range_sloc[symbol] = vr_sloc
        else:
            old = self.var_to_range[symbol]
            new = old & vr
            if new != old:
                if vr_sloc is None:
                    sloc = self._get_sloc()
                    vr_sloc = ValueRangesSLoc(sloc, sloc)
                if new.lower != old.lower:
                    self.var_to_range_sloc[symbol].lower = vr_sloc.lower
                if new.upper != old.upper:
                    self.var_to_range_sloc[symbol].upper = vr_sloc.upper
                self.var_to_range[symbol] = new
                self.log.debug("_update_var_to_range %s = %s (update)", symbol, new)

        if (v := self.backed_var_to_val.get(symbol)) is not None:
            r = self.var_to_range[symbol]
            if v not in r:
                # For constraint failure, delay this for later
                # TODO: Rework all of this, the constraint logic is very
                # duplicative with regular reasoning
                if not is_constraint:
                    if v not in r:
                        raise AssertionError(f"{v} not in {r}")