def node_to_str(node) -> CodeBlockInfo | None:
        """
        Parses and converts an Abstract Syntax Tree (AST) node to a CodeBlockInfo object.

        Args:
            node: The AST node to be converted.

        Returns:
            CodeBlockInfo | None: A CodeBlockInfo object representing the parsed AST node,
                                  or None if the conversion fails.
        """
        if isinstance(node, ast.Try):
            return None
        if any_to_str(node) == any_to_str(ast.Expr):
            return CodeBlockInfo(
                lineno=node.lineno,
                end_lineno=node.end_lineno,
                type_name=any_to_str(node),
                tokens=RepoParser._parse_expr(node),
            )
        mappings = {
            any_to_str(ast.Import): lambda x: [RepoParser._parse_name(n) for n in x.names],
            any_to_str(ast.Assign): RepoParser._parse_assign,
            any_to_str(ast.ClassDef): lambda x: x.name,
            any_to_str(ast.FunctionDef): lambda x: x.name,
            any_to_str(ast.ImportFrom): lambda x: {
                "module": x.module,
                "names": [RepoParser._parse_name(n) for n in x.names],
            },
            any_to_str(ast.If): RepoParser._parse_if,
            any_to_str(ast.AsyncFunctionDef): lambda x: x.name,
            any_to_str(ast.AnnAssign): lambda x: RepoParser._parse_variable(x.target),
        }
        func = mappings.get(any_to_str(node))
        if func:
            code_block = CodeBlockInfo(lineno=node.lineno, end_lineno=node.end_lineno, type_name=any_to_str(node))
            val = func(node)
            if isinstance(val, dict):
                code_block.properties = val
            elif isinstance(val, list):
                code_block.tokens = val
            elif isinstance(val, str):
                code_block.tokens = [val]
            else:
                raise NotImplementedError(f"Not implement:{val}")
            return code_block
        logger.warning(f"Unsupported code block:{node.lineno}, {node.end_lineno}, {any_to_str(node)}")
        return None