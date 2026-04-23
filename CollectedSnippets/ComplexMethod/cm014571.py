def is_view_op(self) -> bool:
        rets = self.func.returns
        is_non_mutating_view = len(rets) > 0 and any(
            r.annotation is not None and not r.annotation.is_write for r in rets
        )
        # See Note [resize_ in Functionalization] for more dtails
        is_inplace_view = (
            "inplace_view" in self.tags
            and str(self.func.name) != "resize_"
            and str(self.func.name) != "resize_as_"
        )
        is_wildcard_view = any(
            inp.annotation is not None and "*" in inp.annotation.alias_set_after
            for inp in self.func.schema_order_arguments()
        )
        return is_non_mutating_view or is_inplace_view or is_wildcard_view