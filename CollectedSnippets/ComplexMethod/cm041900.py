def _parse_if(n):
        """
        Parses an 'if' statement Abstract Syntax Tree (AST) node.

        Args:
            n: The AST node representing an 'if' statement.

        Returns:
            None or Parsed information from the 'if' statement node.
        """
        tokens = []
        try:
            if isinstance(n.test, ast.BoolOp):
                tokens = []
                for v in n.test.values:
                    tokens.extend(RepoParser._parse_if_compare(v))
                return tokens
            if isinstance(n.test, ast.Compare):
                v = RepoParser._parse_variable(n.test.left)
                if v:
                    tokens.append(v)
            if isinstance(n.test, ast.Name):
                v = RepoParser._parse_variable(n.test)
                tokens.append(v)
            if hasattr(n.test, "comparators"):
                for item in n.test.comparators:
                    v = RepoParser._parse_variable(item)
                    if v:
                        tokens.append(v)
            return tokens
        except Exception as e:
            logger.warning(f"Unsupported if: {n}, err:{e}")
        return tokens