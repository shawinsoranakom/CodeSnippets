def _validate(self) -> None:
            if len(self._source_exprs) == 0 or len(self._target_exprs) == 0:
                # If there are no source/target expressions, there's nothing we really
                # wish to prove. So, we just return.
                return None

            # Here, we use "QF_NRA" logic for the solver:
            #   "Quantifier-free Non-linear Real Arithmetic".
            #
            # Most of the guards expressions have:
            #   1. arithmetic between integer and reals
            #   2. no quantifiers
            #   3. potentially non-linear.
            #
            # Although there's also "QF_NIRA" (mixed integer-real arithmetic),
            # "QF_NRA" seems to work better on 'dynamo/test_dynamic_shapes.py'.
            solver = z3.SolverFor("QF_NRA")
            # Set a timeout for finding a solution.
            solver.set(timeout=translation_validation_timeout())

            # Add all the assertions to the solver.
            for assertion in self._assertions:
                solver.add(assertion)

            # "Is there any case where it's TRUE for the target expressions,
            #  but FALSE for the source expressions?"
            solver.add(z3.Not(z3.And(*self._source_exprs)))
            solver.add(*self._target_exprs)

            log.debug("translation validation: start")
            r = solver.check()
            if r == z3.sat:
                # Target expressions are unsound.
                # Log the found model and the source expressions that failed.
                model = solver.model()
                raise ValidationException(
                    model,
                    self._assertions,
                    self._target_exprs,
                    failed_source_exprs=[
                        inp for inp in self._source_exprs if not model.evaluate(inp)
                    ],
                )
            else:
                if r == z3.unknown:
                    # Could not find a solution. It didn't fail, but it also
                    # didn't succeed. Canceling the validation execution (keyboard
                    # interrupt) also gets to this branch.
                    log.warning(
                        "translation validation: could not validate: got z3.unknown"
                    )
                else:
                    # Target expressions are sound.
                    if r != z3.unsat:
                        raise AssertionError(f"Expected z3.unsat, got {r}")
                    log.debug("translation validation: success")