def call_method(
        self,
        tx: "InstructionTranslator",
        name: str,
        args: list[VariableTracker],
        kwargs: dict[str, VariableTracker],
    ) -> VariableTracker:
        from .builder import SourcelessBuilder

        if name == "__iter__":
            if not all(var.is_python_constant() for var in self.items):
                # Can't represent a `range_iterator` without well defined bounds
                return variables.misc.DelayGraphBreakVariable(
                    msg="Cannot create range_iterator: bounds (start, stop, step) must be fully defined as concrete constants.",
                )
            return RangeIteratorVariable(
                self.start(), self.stop(), self.step(), self.range_length()
            )
        elif name in ("count", "__contains__"):
            return SourcelessBuilder.create(tx, self.range_count(*args))
        elif name == "index":
            x = args[0].as_python_constant()
            start, stop, step = self.start(), self.stop(), self.step()
            in_range = (start <= x < stop) if step > 0 else (stop < x <= start)
            if in_range and ((x - start) % step) == 0:
                return VariableTracker.build(tx, (x - start) // step)
            raise_observed_exception(
                ValueError,
                tx,
                args=[f"{x} is not in range"],
            )
        elif name in cmp_name_to_op_mapping:
            other = args[0]
            pt = other.python_type()
            if name not in ("__eq__", "__ne__"):
                msg = f"{name} not supported between instances of 'range' and '{pt}'"
                raise_observed_exception(
                    TypeError,
                    tx,
                    args=[msg],
                )

            if pt is not range:
                return VariableTracker.build(tx, NotImplemented)

            if isinstance(other, RangeVariable):
                cmp = self.range_equals(other)
            else:
                cmp = False

            # Two ranges are equal if they produce the same sequence of values
            if name == "__eq__":
                return SourcelessBuilder.create(tx, cmp)
            else:
                return SourcelessBuilder.create(tx, not cmp)
        return super().call_method(tx, name, args, kwargs)