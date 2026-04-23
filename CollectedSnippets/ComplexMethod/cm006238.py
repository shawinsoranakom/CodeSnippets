def validate_migration_file(self, filepath: Path) -> dict[str, Any]:
        """Validate a single migration file."""
        if not filepath.exists():
            return {
                "file": str(filepath),
                "valid": False,
                "violations": [Violation("FILE_NOT_FOUND", f"File not found: {filepath}", 0)],
                "warnings": [],
            }

        content = filepath.read_text()

        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            return {
                "file": str(filepath),
                "valid": False,
                "violations": [Violation("SYNTAX_ERROR", str(e), e.lineno or 0)],
                "warnings": [],
            }

        violations = []
        warnings = []

        # Check for phase documentation
        phase = self._extract_phase(content)
        if phase == MigrationPhase.UNKNOWN:
            violations.append(
                Violation("NO_PHASE_MARKER", "Migration must specify phase: EXPAND, MIGRATE, or CONTRACT", 1)
            )

        # Check upgrade function
        upgrade_node = self._find_function(tree, "upgrade")
        if upgrade_node:
            phase_violations = self._check_upgrade_operations(upgrade_node, phase)
            violations.extend(phase_violations)
        else:
            violations.append(Violation("MISSING_UPGRADE", "Migration must have an upgrade() function", 1))

        # Check downgrade function
        downgrade_node = self._find_function(tree, "downgrade")
        if downgrade_node:
            downgrade_issues = self._check_downgrade_safety(downgrade_node, phase)
            warnings.extend(downgrade_issues)
        elif phase != MigrationPhase.CONTRACT:  # CONTRACT phase may not support rollback
            violations.append(Violation("MISSING_DOWNGRADE", "Migration must have a downgrade() function", 1))

        # Additional phase-specific checks
        if phase == MigrationPhase.CONTRACT:
            contract_issues = self._check_contract_phase_requirements(content)
            violations.extend(contract_issues)

        return {
            "file": str(filepath),
            "valid": len(violations) == 0,
            "violations": [v.__dict__ for v in violations],
            "warnings": [w.__dict__ for w in warnings],
            "phase": phase.value,
        }