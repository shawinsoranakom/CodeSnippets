def main():
    parser = argparse.ArgumentParser(
        description='Database Schema Synchronization Tool using peewee-migrate',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all migrations
  python db_schema_sync.py --list --host localhost --port 3306 --user root --password xxx --database rag_flow --version v0.25.0

  # Create migration from model changes
  python db_schema_sync.py --create --host localhost --port 3306 --user root --password xxx --database rag_flow --version v0.25.0

  # Create migration including dropped fields (destructive!)
  python db_schema_sync.py --create --drop --host localhost --port 3306 --user root --password xxx --database rag_flow --version v0.25.0

  # Run all pending migrations
  python db_schema_sync.py --migrate --host localhost --port 3306 --user root --password xxx --database rag_flow --version v0.25.0

  # Show schema differences
  python db_schema_sync.py --diff --host localhost --port 3306 --user root --password xxx --database rag_flow --version v0.25.0
"""
    )

    # Database connection options
    parser.add_argument('--host', type=str, required=True, help='MySQL host')
    parser.add_argument('--port', type=int, default=3306, help='MySQL port (default: 3306)')
    parser.add_argument('--user', type=str, required=True, help='MySQL user')
    parser.add_argument('--password', type=str, required=True, help='MySQL password')
    parser.add_argument('--database', type=str, required=True, help='MySQL database name')

    # Version option
    parser.add_argument('--version', '-v', type=str, required=True, 
                       help='Version number in format vxx.xx.xx (e.g., v0.25.0)')

    # Action options
    parser.add_argument('--list', '-l', action='store_true', help='List all migrations')
    parser.add_argument('--create', '-c', action='store_true', 
                       help='Create migration from model changes (auto-detect)')
    parser.add_argument('--migrate', '-m', action='store_true', help='Run pending migrations')
    parser.add_argument('--diff', '-d', action='store_true', help='Show schema differences')

    # Migration options
    parser.add_argument('--name', '-n', type=str, default='auto', help='Migration name')
    parser.add_argument('--drop', action='store_true',
                       help='Include DROP COLUMN for fields removed from models (destructive - will permanently delete data!)')

    args = parser.parse_args()

    # Validate version format
    if not validate_version(args.version):
        logger.error(f"Invalid version format: {args.version}. Expected format: vxx.xx.xx (e.g., v0.25.0)")
        sys.exit(1)

    # Validate at least one action is specified
    if not any([args.list, args.create, args.migrate, args.diff]):
        parser.print_help()
        logger.error("Please specify at least one action: --list, --create, --migrate, or --diff")
        sys.exit(1)

    # Convert version to directory name
    version_dir = version_to_dirname(args.version)
    migrate_dir = os.path.join(PROJECT_BASE, 'tools', 'migrate', version_dir)

    logger.info(f"Version: {args.version}")
    logger.info(f"Migration directory: {migrate_dir}")

    # Create migration directory if it doesn't exist
    os.makedirs(migrate_dir, exist_ok=True)

    # Load database models
    logger.info("Loading database models from api/db/db_models.py...")
    models, _ = load_db_models()
    logger.info(f"Found {len(models)} model classes")

    # Create database connection
    db = create_database_connection(
        host=args.host,
        port=args.port,
        user=args.user,
        password=args.password,
        database=args.database
    )

    try:
        db.connect()
        logger.info(f"Connected to database: {args.database}")

        # Create router
        router = Router(
            db,
            migrate_dir,
            ignore=['basemodel', 'base_model', 'migratehistory']
        )

        # Execute requested actions
        if args.list:
            list_migrations(router)

        if args.create:
            create_migration(router, models, db, args.name, drop_fields=args.drop)

        if args.migrate:
            run_migrations(router)

        if args.diff:
            diff_schema(models, db)

    finally:
        if not db.is_closed():
            db.close()
            logger.info("Database connection closed")

    logger.info("Done.")