def lookahead_call_helper(self, node: Lookahead, positive: int) -> FunctionCall:
        call = self.generate_call(node.node)
        comment = None
        if call.nodetype is NodeTypes.NAME_TOKEN:
            function = "_PyPegen_lookahead_for_expr"
            self.assert_no_undefined_behavior(call, function, "expr_ty")
        elif call.nodetype is NodeTypes.STRING_TOKEN:
            # _PyPegen_string_token() returns 'void *' instead of 'Token *';
            # in addition, the overall function call would return 'expr_ty'.
            assert call.function == "_PyPegen_string_token"
            function = "_PyPegen_lookahead"
            self.assert_no_undefined_behavior(call, function, "expr_ty")
        elif call.nodetype == NodeTypes.SOFT_KEYWORD:
            function = "_PyPegen_lookahead_with_string"
            self.assert_no_undefined_behavior(call, function, "expr_ty")
        elif call.nodetype in {NodeTypes.GENERIC_TOKEN, NodeTypes.KEYWORD}:
            function = "_PyPegen_lookahead_with_int"
            self.assert_no_undefined_behavior(call, function, "Token *")
            comment = f"token={node.node}"
        elif call.return_type == "expr_ty":
            function = "_PyPegen_lookahead_for_expr"
        elif call.return_type == "stmt_ty":
            function = "_PyPegen_lookahead_for_stmt"
        else:
            function = "_PyPegen_lookahead"
            self.assert_no_undefined_behavior(call, function, None)
        return FunctionCall(
            function=function,
            arguments=[positive, call.function, *call.arguments],
            return_type="int",
            comment=comment,
        )