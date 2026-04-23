def _allowable(self, node: nodes.NodeNG) -> bool:
        scope = node.scope()
        if isinstance(scope, nodes.FunctionDef) and (scope.name.startswith("_") or scope.name == 'init'):
            return True

        infered = utils.safe_infer(node)
        # The package 'psycopg2' must be installed to infer
        # ignore sql.SQL().format or variable that can be infered as constant
        if infered and infered.pytype().startswith('psycopg2'):
            return True
        if self._is_constexpr(node):  # If we can infer the value at compile time, it cannot be injected
            return True

        # self._thing is OK (mostly self._table), self._thing() also because
        # it's a common pattern of reports (self._select, self._group_by, ...)
        return (isinstance(node, nodes.Attribute)
            and isinstance(node.expr, nodes.Name)
            and node.attrname.startswith('_')
        )