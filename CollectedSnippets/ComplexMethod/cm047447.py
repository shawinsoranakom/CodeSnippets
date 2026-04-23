def _is_constexpr(self, node: nodes.NodeNG, *, args_allowed=False, position=None):
        if isinstance(node, nodes.Const):  # astroid.const is always safe
            return True
        elif isinstance(node, (nodes.List, nodes.Set)):
            return self.all_const(node.elts, args_allowed=args_allowed)
        elif isinstance(node, nodes.Tuple):
            if position is None:
                return self.all_const(node.elts, args_allowed=args_allowed)
            else:
                return self._is_constexpr(node.elts[position], args_allowed=args_allowed)
        elif isinstance(node, nodes.Dict):
            return all(
                self._is_constexpr(k, args_allowed=args_allowed) and self._is_constexpr(v, args_allowed=args_allowed)
                for k, v in node.items
            )
        elif isinstance(node, nodes.Starred):
            return self._is_constexpr(node.value, args_allowed=args_allowed, position=position)
        elif isinstance(node, nodes.BinOp):  # recusively infer both side of the operation. Failing if either side is not inferable
            left_operand = self._is_constexpr(node.left, args_allowed=args_allowed)
            # This case allows to always consider a string formatted with %d to be safe
            if node.op == '%' and \
                isinstance(node.left, nodes.Const) and \
                node.left.pytype() == 'builtins.str' and \
                '%d' in node.left.value and \
                not '%s' in node.left.value:
                return True
            right_operand = self._is_constexpr(node.right, args_allowed=args_allowed)
            return left_operand and right_operand
        elif isinstance(node, (nodes.Name, nodes.AssignName)):  # Variable: find the assignement instruction in the AST and infer its value.
            assignment = node.lookup(node.name)
            assigned_node = []
            for n in assignment[1]:  # assignment[0] contains the scope, so assignment[1] contains the assignement nodes
                # FIXME: makes no sense, assuming this gets
                #        `visit_functiondef`'d we should just ignore it
                if isinstance(n.parent, (nodes.FunctionDef, nodes.Arguments)):
                    assigned_node += [args_allowed]
                elif isinstance(n.parent, nodes.Tuple):  # multi assign a,b = (a,b)
                    statement = n.statement()
                    if isinstance(statement, nodes.For):
                        assigned_node += [self._is_constexpr(statement.iter, args_allowed=args_allowed)]
                    elif isinstance(statement, nodes.Assign):
                        assigned_node += [self._is_constexpr(statement.value, args_allowed=args_allowed, position=n.parent.elts.index(n))]
                    else:
                        raise TypeError(f"Expected statement Assign or For, got {statement}")
                elif isinstance(n.parent, nodes.For):
                    assigned_node.append(self._is_constexpr(n.parent.iter, args_allowed=args_allowed))
                elif isinstance(n.parent, nodes.AugAssign):
                    left = self._is_constexpr(n.parent.target, args_allowed=args_allowed)
                    right = self._is_constexpr(n.parent.value, args_allowed=args_allowed)
                    assigned_node.append(left and right)
                elif isinstance(n.parent, nodes.Module):
                    return True
                else:
                    if isinstance(n.parent, nodes.Comprehension):
                        assigned_node += [self._is_constexpr(n.parent.iter, args_allowed=args_allowed)]
                    else:
                        assigned_node += [self._is_constexpr(n.parent.value, args_allowed=args_allowed)]
            if assigned_node and all(assigned_node):
                return True
            return self._is_asserted(node)
        elif isinstance(node, nodes.JoinedStr):
            return self._is_fstring_cst(node, args_allowed)
        elif isinstance(node, nodes.Call):
            if isinstance(node.func, nodes.Attribute):
                if node.func.attrname == 'append':
                    return self._is_constexpr(node.args[0])
                elif node.func.attrname == 'format':
                    return (
                        self._is_constexpr(node.func.expr, args_allowed=args_allowed)
                    and self.all_const(node.args, args_allowed=args_allowed)
                    and self.all_const((key.value for key in node.keywords or []), args_allowed=args_allowed)
                    )
            with push_call(node):
                return self._evaluate_function_call(node, args_allowed=args_allowed, position=position)
        elif isinstance(node, nodes.IfExp):
            body = self._is_constexpr(node.body, args_allowed=args_allowed)
            orelse = self._is_constexpr(node.orelse, args_allowed=args_allowed)
            return body and orelse
        elif isinstance(node, nodes.Subscript):
            return self._is_constexpr(node.value, args_allowed=args_allowed)
        elif isinstance(node, nodes.BoolOp):
            return self.all_const(node.values, args_allowed=args_allowed)

        elif isinstance(node, nodes.Attribute):
            attr_chain = self._get_attribute_chain(node)
            while attr_chain:
                if attr_chain in ATTRIBUTE_WHITELIST or attr_chain.startswith('_'):
                    return True
                if '.' in attr_chain:
                    _, attr_chain = attr_chain.split('.', 1)
                else:
                    break
            return False
        return False