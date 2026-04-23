def _parse_type_promotion_rule_from_refs_op(
        cls,
        decorated_op: Callable,
    ) -> ElementwiseTypePromotionRule | None:
        """Retrieve and parse type promotion decorator from op under torch._refs."""
        fn = decorated_op
        type_promo_wrapper = None
        while fn_closure_vars := _try_getclosurevars(fn):
            if "fn" not in fn_closure_vars.nonlocals:
                break
            if "self" in fn_closure_vars.nonlocals and isinstance(
                fn_closure_vars.nonlocals["self"],
                _prims_common_wrappers.elementwise_type_promotion_wrapper,
            ):
                type_promo_wrapper = fn_closure_vars.nonlocals["self"]
                break
            fn = fn_closure_vars.nonlocals["fn"]

        if type_promo_wrapper is not None:
            signature = inspect.signature(decorated_op)

            pos = 0
            promote_args_positions = []
            promote_kwargs_names = []

            if type_promo_wrapper.type_promoting_arg_names is not None:
                for name, param in signature.parameters.items():
                    if name in type_promo_wrapper.type_promoting_arg_names:
                        if param.kind in (
                            param.POSITIONAL_OR_KEYWORD,
                            param.POSITIONAL_ONLY,
                        ):
                            promote_args_positions.append(pos)
                        elif param.kind == param.KEYWORD_ONLY:
                            promote_kwargs_names.append(name)
                    pos += 1

            return ElementwiseTypePromotionRule(
                "aten",
                decorated_op.__name__,
                promote_args_positions=promote_args_positions,
                promote_kwargs_names=promote_kwargs_names,
                promotion_kind=type_promo_wrapper.type_promotion_kind,
            )

        logger.warning(
            "Cannot find type promotion rule for: %s.%s",
            decorated_op.__module__,
            decorated_op.__name__,
        )
        return None