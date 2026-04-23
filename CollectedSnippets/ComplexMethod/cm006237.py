def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Validate Alembic migrations")
    parser.add_argument("files", nargs="+", help="Migration files to validate")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as errors")

    args = parser.parse_args()

    validator = MigrationValidator(strict_mode=args.strict)
    all_valid = True
    results = []

    for file_path in args.files:
        result = validator.validate_migration_file(Path(file_path))
        results.append(result)

        if not result["valid"]:
            all_valid = False

        if args.strict and result["warnings"]:
            all_valid = False

    import logging

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("migration_validator")
    if args.json:
        import sys as _sys

        _sys.stdout.write(json.dumps(results, indent=2) + "\n")
    else:
        for result in results:
            logger.info("\n%s", "=" * 60)
            logger.info("File: %s", result["file"])
            logger.info("Phase: %s", result["phase"])
            logger.info("Valid: %s", "✅" if result["valid"] else "❌")

            if result["violations"]:
                logger.error("\n❌ Violations:")
                for v in result["violations"]:
                    logger.error("  Line %s: %s - %s", v["line"], v["type"], v["message"])

            if result["warnings"]:
                logger.warning("\n⚠️  Warnings:")
                for w in result["warnings"]:
                    logger.warning("  Line %s: %s - %s", w["line"], w["type"], w["message"])

    sys.exit(0 if all_valid else 1)