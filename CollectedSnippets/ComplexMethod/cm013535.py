def _set_replacement(self, a: sympy.Symbol, tgt: sympy.Expr, msg: str) -> None:
        """
        Adds or updates a replacement for a symbol.
        Use this instead of `self.replacements[a] = tgt`.
        """

        if tgt == self.replacements.get(a, None):
            return

        if a in tgt.free_symbols:
            return

        # Precondition: a == tgt
        if not isinstance(a, sympy.Symbol):
            raise AssertionError(f"Expected sympy.Symbol, got {type(a)}")

        if (
            self.prefer_deferred_runtime_asserts_over_guards
            and not _is_supported_equivalence(tgt)
        ):
            return  # continuing leads to placeholder shapes having complex expressions that we can't resolve

        # Handles nested tensor symbolic variables which don't have
        # var_to_range bounds
        tgt_bound = None
        if a in self.var_to_range:
            src_bound = self.var_to_range[a]

            # First, refine the value range of a based on the computed value range
            # of tgt.  This is always OK to do, even if we decide not to do the
            # substitution in the end.  This might be a no-op, if a already has
            # a tighter bound
            tgt_bound = self.bound_sympy(tgt)
            self._update_var_to_range(a, tgt_bound)

            # Next, check if we can update the range of free symbols in tgt
            # based on the range in a. But only do it if:
            #  - the source bound non-trivially improves over what we get out of
            #    the existing bounds.
            #  - the replacement is univariate and we can invert the tgt expression
            if not tgt_bound.issubset(src_bound) and len(tgt.free_symbols) == 1:
                b = next(iter(tgt.free_symbols))
                # Try to invert the equality
                r = try_solve(sympy.Eq(a, tgt), b, floordiv_inequality=False)
                if r is not None:
                    self.log.debug(
                        "set_replacement: solve for %s in %s == %s gives %s",
                        b,
                        a,
                        tgt,
                        r,
                    )
                    # The solution here can be non-integral, for example, if
                    # we have s0 = 2*s1, then s1 = s0/2.  What we would like
                    # to do is calculated the bounds in arbitrary precision,
                    # and then requantize the bound to integers when we are
                    # done.
                    rat_b_bound = self.bound_sympy(r[1])
                    b_bound = ValueRanges(
                        CeilToInt(rat_b_bound.lower), FloorToInt(rat_b_bound.upper)
                    )
                    self._update_var_to_range(b, b_bound, self.var_to_range_sloc[a])
                    tgt_bound = self.bound_sympy(tgt)
                    if not tgt_bound.issubset(src_bound):
                        raise AssertionError(
                            f"{tgt_bound=} not a subset of {src_bound=}"
                        )

            # TODO: Should we propagate size-like-ness?
            #
            # Pros: if u0 is size-like, intuitively u0 == u1 should cause u1
            # to become size-like.
            #
            # Cons: if u0 is size-like, what about u0 - 1 == u1?  You CAN'T
            # propagate in this case, because what if u0 == 0, then u1 is negative
            # and clearly isn't a size.  So, at minimum, any f(x) whose value
            # range isn't [0, inf] given x in [0, inf] cannot propagate
            # size-like-ness.  But there are many situations where you could
            # imagine u1 is going to be size-like and actually you just didn't
            # have a refined enough value range on u0.  Since even innocuous
            # looking arithmetic operations can destroy size-like-ness, it's
            # best to not propagate it at all and force the user to annotate it
            # as necessary.
            #
            # Compromise: we preserve size-like-ness only for exact equality
            # and nothing else.
            if a in self.size_like and isinstance(tgt, sympy.Symbol):
                self.size_like.add(tgt)
            elif isinstance(tgt, sympy.Symbol) and tgt in self.size_like:
                self.size_like.add(a)

            # Now, decide if we will do the substitution.
            #
            #  - If the source has a non-trivial range, only substitute if
            #    we preserve this range.  Note that we may have propagated
            #    the src_range to free variables in tgt when tgt is univariate
            #    and we could find an inverse, which helps us achieve this.
            #    This ensures we never "forget" about user defined ranges,
            #    even if they end up being defined on composite formulas
            #    like s0 + s1.
            #
            #  - If the variable is unbacked, only substitute if the substitution
            #    would preserve the bounds also under size-like-ness conditions.

            if not tgt_bound.issubset(src_bound):
                self.log.debug(
                    "skipped set_replacement %s = %s (%s) [%s not subset of %s]",
                    a,
                    tgt,
                    msg,
                    tgt_bound,
                    src_bound,
                )
                return
            elif a in self.size_like:
                tgt_bound_so = self.bound_sympy(tgt, size_oblivious=True)
                src_bound_so = self.bound_sympy(a, size_oblivious=True)
                if not tgt_bound_so.issubset(src_bound_so):
                    self.log.debug(
                        "skipped set_replacement %s = %s (%s) "
                        "[%s not subset of %s (size-oblivious conditions)]",
                        a,
                        tgt,
                        msg,
                        tgt_bound_so,
                        src_bound_so,
                    )
                    return

        if isinstance(tgt, (sympy.Integer, sympy.Float)):
            # specializing to a constant, which is likely unexpected (unless
            # you specified dynamic=True)

            user_tb = TracingContext.extract_stack()
            trace_structured(
                "symbolic_shape_specialization",
                metadata_fn=lambda: {
                    "symbol": repr(a),
                    "sources": [s.name for s in self.var_to_sources.get(a, [])],
                    "value": repr(tgt),
                    "reason": msg,
                    "stack": structured.from_traceback(
                        CapturedTraceback.extract(skip=1).summary()
                    ),
                    "user_stack": (
                        structured.from_traceback(user_tb) if user_tb else None
                    ),
                },
            )

            for source in self.var_to_sources.get(a, []):
                if user_tb:
                    self.specialization_stacks[source] = user_tb

            if config.print_specializations:
                self.log.warning(
                    "Specializing %s to %s", self.var_to_sources[a][0].name, tgt
                )
                self.log.debug("SPECIALIZATION", stack_info=True)
        log.info("set_replacement %s = %s (%s) %s", a, tgt, msg, tgt_bound)
        self.replacements[a] = tgt
        # NB: the replacement may get refined, but the user will find the
        # FIRST one most useful (TODO: Maybe we could consider tracking all of
        # them)
        if a not in self.replacements_slocs:
            self.replacements_slocs[a] = self._get_sloc()
        self._replacements_version_counter += 1
        self._update_version_counter()

        # When specializing 'a == tgt', the equality should be also conveyed to
        # Z3, in case an expression uses 'a'.
        self._add_target_expr(sympy.Eq(a, tgt, evaluate=False))