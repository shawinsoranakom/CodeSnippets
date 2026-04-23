def cmd_views(args: argparse.Namespace) -> None:
    only = [v.strip() for v in args.only.split(",")] if args.only else None
    views = load_views(only=only)
    if not views:
        print("No matching views found.")
        sys.exit(0)

    if args.dry_run:
        print(f"-- {len(views)} views\n")
        for label, sql in views:
            print(f"-- {label}")
            print(sql)
        return

    db_url = get_db_url(args)
    if not db_url:
        no_db_url_error()
    assert db_url
    print(f"Applying {len(views)} view(s)...")
    # Append grant refresh so the readonly role sees any new views
    grant = f"GRANT SELECT ON ALL TABLES IN SCHEMA {SCHEMA} TO analytics_readonly;"
    run_sql(db_url, views + [("grant analytics_readonly", grant)])