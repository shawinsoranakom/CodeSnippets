def test_legacy_migrations_flagged(self):
        """Ensure legacy migrations are flagged for missing phase markers."""
        workspace_root = Path(__file__).resolve().parents[5]
        migrations_dir = workspace_root / "src/backend/base/langflow/alembic/versions"

        validator = MigrationValidator(strict_mode=False)

        if not migrations_dir.exists():
            pytest.fail(f"Migrations directory not found at {migrations_dir}")

        legacy_migration = next(
            (
                f
                for f in sorted(migrations_dir.glob("*.py"))
                if not f.name.startswith("00") and f.name != "__init__.py" and "Phase:" not in f.read_text()
            ),
            None,
        )

        if legacy_migration is None:
            pytest.skip("All migrations already have phase markers")

        result = validator.validate_migration_file(legacy_migration)
        assert result["valid"] is False
        violations = [v["type"] for v in result["violations"]]
        assert "NO_PHASE_MARKER" in violations