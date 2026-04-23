def migrate(
    ctx,
    es_host,
    es_port,
    es_user,
    es_password,
    es_api_key,
    ob_host,
    ob_port,
    ob_user,
    ob_password,
    ob_database,
    index,
    table,
    batch_size,
    resume,
    verify,
    progress_dir,
):
    """Run RAGFlow data migration from Elasticsearch to OceanBase.

    If --index is omitted, all indices starting with 'ragflow_' will be migrated.
    If --table is omitted, the same name as the source index will be used.
    """
    console.print("[bold]RAGFlow ES to OceanBase Migration[/]")

    try:
        # Initialize ES client first to discover indices if needed
        es_client = ESClient(
            host=es_host,
            port=es_port,
            username=es_user,
            password=es_password,
            api_key=es_api_key,
        )

        ob_client = OBClient(
            host=ob_host,
            port=ob_port,
            user=ob_user,
            password=ob_password,
            database=ob_database,
        )

        # Determine indices to migrate
        if index:
            # Single index specified
            indices_to_migrate = [(index, table if table else index)]
        else:
            # Auto-discover all ragflow_* indices
            console.print("\n[cyan]Discovering RAGFlow indices...[/]")
            ragflow_indices = es_client.list_ragflow_indices()

            if not ragflow_indices:
                console.print("[yellow]No ragflow_* indices found in Elasticsearch[/]")
                sys.exit(0)

            # Each index maps to a table with the same name
            indices_to_migrate = [(idx, idx) for idx in ragflow_indices]

            console.print(f"[green]Found {len(indices_to_migrate)} RAGFlow indices:[/]")
            for idx, _ in indices_to_migrate:
                doc_count = es_client.count_documents(idx)
                console.print(f"  - {idx} ({doc_count:,} documents)")
            console.print()

        # Initialize migrator
        migrator = ESToOceanBaseMigrator(
            es_client=es_client,
            ob_client=ob_client,
            progress_dir=progress_dir,
        )

        # Track overall results
        total_success = 0
        total_failed = 0
        results = []

        # Migrate each index
        for es_index, ob_table in indices_to_migrate:
            console.print(f"\n[bold blue]{'='*60}[/]")
            console.print(f"[bold]Migrating: {es_index} -> {ob_database}.{ob_table}[/]")
            console.print(f"[bold blue]{'='*60}[/]")

            result = migrator.migrate(
                es_index=es_index,
                ob_table=ob_table,
                batch_size=batch_size,
                resume=resume,
                verify_after=verify,
            )

            results.append(result)
            if result["success"]:
                total_success += 1
            else:
                total_failed += 1

        # Summary for multiple indices
        if len(indices_to_migrate) > 1:
            console.print(f"\n[bold]{'='*60}[/]")
            console.print("[bold]Migration Summary[/]")
            console.print(f"[bold]{'='*60}[/]")
            console.print(f"  Total indices: {len(indices_to_migrate)}")
            console.print(f"  [green]Successful: {total_success}[/]")
            if total_failed > 0:
                console.print(f"  [red]Failed: {total_failed}[/]")

        # Exit code based on results
        if total_failed == 0:
            console.print("\n[bold green]All migrations completed successfully![/]")
            sys.exit(0)
        else:
            console.print(f"\n[bold red]{total_failed} migration(s) failed[/]")
            sys.exit(1)

    except Exception as e:
        console.print(f"[bold red]Error: {e}[/]")
        if ctx.obj.get("verbose"):
            console.print_exception()
        sys.exit(1)
    finally:
        # Cleanup
        if "es_client" in locals():
            es_client.close()
        if "ob_client" in locals():
            ob_client.close()