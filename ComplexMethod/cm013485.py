def _make_user_magic(method: str, user_type: type) -> None:
    # User magic takes care of wrapping the other operand into a node,
    # so that our internal logic can assume everything is nodes
    if method in magic_methods_on_operator_with_trailing_underscore:
        method_attr = f"sym_{method}"
    else:
        method_attr = method

    def get_constant(
        x: SymInt | int | SymFloat | float | SymBool | bool,
    ) -> int | float | bool:
        if isinstance(x, (int, float, bool)):
            return x
        if isinstance(x, SymInt):
            return x.node.guard_int("", 0)
        if isinstance(x, SymBool):
            return x.node.guard_bool("", 0)
        raise AssertionError("expect to be called with constant SymBools")

    def is_constant(x: SymInt | int | SymFloat | float | SymBool | bool) -> bool:
        if isinstance(x, (int, float, bool)):
            return True
        if isinstance(x, (SymInt, SymFloat, SymBool)):
            return x.node.is_constant()
        return False

    # Promotion rules for binary operations.  NB: we preserve PYTHON semantics
    #   - if args are same type, do nothing
    #   - if one arg is float, promote other arg to float
    #       - nb: this applies to floordiv, even though output is integral
    #       (it's still float)
    #   - pow is funny business
    #       - if both ints
    #       - trigger a guard on exponent >= 0
    #           - if non-negative, output is int
    #           - otherwise, output is float
    #   - otherwise, promote other arg to float
    #       - nb: complex is impossible to handle correctly lol, with
    #       negative base and integral float need to diverge semantics and
    #       just always return complex.  Neener neener pretend this problem
    #       doesn't exist
    #   - equality is pain: Python does the fancy thing where it unpacks the
    #     mantissa from the float and then compares that against the int.
    #     Which means it is able to tell that
    #     9007199254740993 != 9007199254740992. (rather than if the LHS was
    #     promoted to float, in which case it would have truncated to the RHS
    #     and subsequently been equal).  We'll model this exactly by having
    #     special mixed type equality operations.  Unfortunately, we need to
    #     do this for all comparison operations (maybe I'll only implement
    #     compare)
    #   - sym_ite mumble mumble really shouldn't allow mixed but whatever

    if method in bool_becomes_int_magic_methods:

        def promote(x: object) -> Any:
            """Implements True+True=2, which works in python but not sympy"""
            if isinstance(x, SymBool):
                return SymInt(x.node.wrap_int(int(x)))
            return x

    else:

        def promote(x: object) -> Any:
            return x

    def promote2(self: object, other: object) -> tuple[Any, Any]:
        # TODO: Remove eq and other relations from this list.
        # CPython has fancy implementations for these to get as much precision
        # as possible instead of just promoting to float64 and praying, so we
        # need to handle them specially too.
        # Also, note that int_truediv doesn't go through this path: both
        # arguments are "int" so there isn't any promotion
        if method not in [
            "add",
            "sub",
            "mul",
            "mod",
            "float_pow",
            "float_truediv",
            "int_floordiv",
            "sym_min",
            "sym_max",
            # TODO: remove these
            "eq",
            "ne",
            "gt",
            "lt",
            "le",
            "ge",
        ]:
            return self, other
        f_self = isinstance(self, (float, torch.SymFloat))
        f_other = isinstance(other, (float, torch.SymFloat))
        if f_self or f_other:
            if not f_self:
                self = torch.sym_float(self)
            if not f_other:
                other = torch.sym_float(other)
        return self, other

    # Before and after performing the operation, check if any operands are constant.
    # If so, extract out the constant values first. If `self` itself is a
    # constant, then "redispatch" by calling back into the operator. Sometimes
    # this means that operations involving SymBool return plain bools.
    # Alternatively, we could also rewrap into constant Symbool (i.e. by
    # implementing wrap_bool in ConstantSymNodeImpl), but we're not doing that
    # today for no particular reason.
    def unary_magic_impl(self: object) -> Any:
        self = promote(self)
        if is_constant(self):
            return (method_to_operator(method))(get_constant(self))
        return wrap_node(getattr(self.node, method_attr)())

    def binary_magic_impl(self: object, other: object) -> Any:
        if not isinstance(other, (int, float, bool, SymInt, SymFloat, SymBool)):
            return NotImplemented
        sym_node_log.debug("MAGIC %s %s %s", method, self, other)
        self = promote(self)
        other = promote(other)
        self, other = promote2(self, other)
        if is_constant(self):
            return (method_to_operator(method))(get_constant(self), other)
        if is_constant(other):
            other = get_constant(other)
        other_node = to_node(self.node, other)
        if other_node is NotImplemented:
            return NotImplemented
        ret = wrap_node(getattr(self.node, method_attr)(other_node))
        return get_constant(ret) if is_constant(ret) else ret

    def rbinary_magic_impl(self: object, other: object) -> Any:
        if not isinstance(other, (int, float, bool, SymInt, SymFloat, SymBool)):
            return NotImplemented
        self = promote(self)
        other = promote(other)
        self, other = promote2(self, other)
        if is_constant(self):
            return (method_to_operator(method))(other, get_constant(self))
        if is_constant(other):
            other = get_constant(other)
        other_node = to_node(self.node, other)
        if other_node is NotImplemented:
            return NotImplemented
        ret = wrap_node(getattr(other_node, method_attr)(self.node))
        return get_constant(ret) if is_constant(ret) else ret

    def setattrs(user_type: type, attr: str, symnode_impl: object) -> None:
        """
        Registers the SymNode magic method on SymInt/Float/Bool,
        and optionally registers a corresponding wrapped method on DynamicInt.
        """

        # SymInt/Float/Bool
        setattr(user_type, attr, symnode_impl)

        # DynamicInt impl
        def dynamic_int_impl(*args: object) -> Any:
            args = [  # pyrefly: ignore[bad-assignment]
                x.real if isinstance(x, DynamicInt) else x for x in args
            ]
            out = getattr(int, attr)(*args)
            if isinstance(out, int) and not isinstance(out, bool):
                return DynamicInt(out)
            return out

        if user_type is SymInt:
            setattr(DynamicInt, attr, dynamic_int_impl)

    if method in unary_magic_methods:
        setattrs(user_type, f"__{method}__", unary_magic_impl)
    elif method in unary_nonmagic_methods:
        orig = getattr(user_type, method)
        setattrs(user_type, method, update_wrapper(unary_magic_impl, orig))
    elif method == "sym_ite":

        def sym_ite_magic_impl(
            pred: SymBool, then_val: object, else_val: object
        ) -> Any:
            pred_node = pred.node
            then_node = to_node(pred_node, then_val)
            else_node = to_node(pred_node, else_val)
            if then_node is NotImplemented or else_node is NotImplemented:
                return NotImplemented
            if not (
                isinstance(then_node, SymNode)
                and isinstance(else_node, SymNode)
                and then_node.pytype == else_node.pytype
            ):
                raise AssertionError(
                    "then_node and else_node must be SymNodes with same pytype"
                )
            ret = wrap_node(getattr(pred.node, method_attr)(then_node, else_node))
            return (
                get_constant(ret)
                # pyrefly: ignore[missing-attribute]
                if ret.node.is_constant()
                else ret
            )

        setattrs(user_type, f"__{method}__", sym_ite_magic_impl)
    elif method == "round":

        def round_magic_impl(self: SymFloat, ndigits: int | None = None) -> Any:
            if is_constant(self):
                return builtins.round(get_constant(self), ndigits)

            return wrap_node(getattr(self.node, method)(ndigits))

        setattrs(user_type, f"__{method}__", round_magic_impl)
    else:
        method_name = method
        if method in bitwise_ops:
            method_name = bitwise_ops[method]
        setattrs(user_type, f"__{method_name}__", binary_magic_impl)
        if method in reflectable_magic_methods:
            setattrs(user_type, f"__r{method_name}__", rbinary_magic_impl)