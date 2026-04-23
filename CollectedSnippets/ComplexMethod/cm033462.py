def main():
    parser = argparse.ArgumentParser(
        description='MySQL Data Migration Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List available stages
  python mysql_migration.py --list-stages

  # Dry run (default - check only, no write) with config file
  python mysql_migration.py --stages tenant_model_provider --config /path/to/config.yaml

  # Dry run with command line MySQL connection
  python mysql_migration.py --stages tenant_model_provider --host localhost --port 3306 --user root --password secret

  # Create target tables only (no data migration)
  python mysql_migration.py --stages tenant_model_provider --config /path/to/config.yaml --create-table-only

  # Execute full migration (create tables and migrate data)
  python mysql_migration.py --stages tenant_model_provider --config /path/to/config.yaml --execute

  # Run multiple stages
  python mysql_migration.py --stages stage1,stage2,stage3 --config /path/to/config.yaml --execute
"""
    )

    # MySQL connection options
    parser.add_argument('--host', type=str, default='localhost',
                       help='MySQL host (default: localhost)')
    parser.add_argument('--port', type=int, default=3306,
                       help='MySQL port (default: 3306)')
    parser.add_argument('--user', type=str, default='root',
                       help='MySQL user (default: root)')
    parser.add_argument('--password', type=str, default='',
                       help='MySQL password (default: empty)')
    parser.add_argument('--database', type=str, default='rag_flow',
                       help='MySQL database name (default: rag_flow)')

    # Configuration options
    parser.add_argument('--config', '-c', type=str, help='Path to YAML config file')

    # Migration options
    parser.add_argument('--stages', '-s', type=str, help='Comma-separated list of stages to run')
    parser.add_argument('--list-stages', '-l', action='store_true', help='List available stages')
    parser.add_argument('--execute', '-e', action='store_true', default=False,
                       help='Execute full migration: create tables and migrate data')
    parser.add_argument('--create-table-only', action='store_true', default=False,
                       help='Only create target tables, skip data migration')

    args = parser.parse_args()

    # List stages and exit
    if args.list_stages:
        list_available_stages()
        return

    # Parse stages
    if not args.stages:
        logger.error("No stages specified. Use --stages to specify stages or --list-stages to see available stages.")
        sys.exit(1)

    stages = [s.strip() for s in args.stages.split(',')]

    # Load configuration: command line args take precedence over config file
    if args.config:
        config = MigrationConfig.from_config_file(args.config)
        # Override with command line args if provided
        if args.host != 'localhost':
            config.host = args.host
        if args.port != 3306:
            config.port = args.port
        if args.user != 'root':
            config.user = args.user
        if args.password != '':
            config.password = args.password
        if args.database != 'rag_flow':
            config.database = args.database
    else:
        # Use command line args directly
        config = MigrationConfig(
            host=args.host,
            port=args.port,
            user=args.user,
            password=args.password,
            database=args.database
        )

    logger.info(f"MySQL Configuration: host={config.host}, port={config.port}, "
               f"user={config.user}, database={config.database}")

    # Three mutually exclusive modes: dry-run (default), create-table-only, execute
    if args.execute and args.create_table_only:
        logger.error("--execute and --create-table-only are mutually exclusive")
        sys.exit(1)

    dry_run = True
    create_table_only = False

    if args.create_table_only:
        logger.info("Running in CREATE TABLE ONLY mode (create tables, no data migration)")
        dry_run = False
        create_table_only = True
    elif args.execute:
        logger.info("Running in EXECUTE mode (create tables and migrate data)")
        dry_run = False
    else:
        logger.info("Running in DRY-RUN mode (check only, no write). "
                   "Use --create-table-only to create tables, or --execute for full migration.")

    run_migration(
        config=config,
        stages=stages,
        dry_run=dry_run,
        create_table_only=create_table_only
    )