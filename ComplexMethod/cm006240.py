def _check_downgrade_safety(self, node: ast.FunctionDef, phase: MigrationPhase) -> list[Violation]:
        """Check downgrade function for safety issues."""
        warnings = []

        # Check if downgrade might lose data
        for child in ast.walk(node):
            if isinstance(child, ast.Call) and self._is_op_call(child, "alter_column"):
                # Check if there's a backup mechanism
                func_content = ast.unparse(node)
                if "backup" not in func_content.lower() and "SELECT" not in func_content:
                    warnings.append(
                        Violation(
                            "UNSAFE_ROLLBACK",
                            "Downgrade drops column without checking/backing up data",
                            child.lineno,
                            severity="warning",
                        )
                    )

        # CONTRACT phase special handling
        if phase == MigrationPhase.CONTRACT:
            func_content = ast.unparse(node)
            if "NotImplementedError" not in func_content and "raise" not in func_content:
                warnings.append(
                    Violation(
                        "UNSAFE_ROLLBACK",
                        "CONTRACT phase downgrade should raise NotImplementedError or handle carefully",
                        node.lineno,
                        severity="warning",
                    )
                )

        return warnings