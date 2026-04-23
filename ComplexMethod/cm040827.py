def _open_query_language_scope(self, parse_tree: ParseTree) -> None:
        production = is_production(parse_tree)
        if production is None:
            raise RuntimeError(f"Cannot expect QueryLanguage definition at depth: {parse_tree}")

        # Extract the QueryLanguage declaration at this ParseTree level, if any.
        query_language = None
        for child in production.children:
            sub_production = is_production(child, ASLParser.RULE_top_layer_stmt) or is_production(
                child, ASLParser.RULE_state_stmt
            )
            if sub_production is not None:
                child = sub_production.children[0]
            sub_production = is_production(child, ASLParser.RULE_query_language_decl)
            if sub_production is not None:
                query_language = self.visit(sub_production)
                break

        # Check this is the initial scope, if so set the initial value to the declaration or the default.
        if not self._query_language_per_scope:
            if query_language is None:
                query_language = QueryLanguage()
        # Otherwise, check for logical conflicts and add the latest or inherited value to as the next scope.
        else:
            top_query_language = self._get_top_level_query_language()
            if query_language is None:
                query_language = top_query_language
            if (
                top_query_language.query_language_mode == QueryLanguageMode.JSONata
                and query_language.query_language_mode == QueryLanguageMode.JSONPath
            ):
                raise ValueError(
                    f"Cannot downgrade from JSONata context to a JSONPath context at: {parse_tree}"
                )

        self._query_language_per_scope.append(query_language)