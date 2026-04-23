def _check_upgrade_operations(self, node: ast.FunctionDef, phase: MigrationPhase) -> list[Violation]:
        """Check upgrade operations for violations."""
        violations = []

        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if self._is_op_call(child, "add_column"):
                    violations.extend(self._check_add_column(child, phase, node))

                elif self._is_op_call(child, "alter_column"):
                    violations.extend(self._check_alter_column(child, phase))

                elif self._is_op_call(child, "drop_column"):
                    violations.extend(self._check_drop_column(child, phase))

                elif self._is_op_call(child, "rename_table") or self._is_op_call(child, "rename_column"):
                    violations.append(
                        Violation("DIRECT_RENAME", "Use expand-contract pattern instead of direct rename", child.lineno)
                    )

        return violations