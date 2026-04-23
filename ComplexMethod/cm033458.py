def schema(ctx, es_host, es_port, es_user, es_password, index, output):
    """Preview RAGFlow schema analysis from ES mapping."""
    try:
        es_client = ESClient(
            host=es_host,
            port=es_port,
            username=es_user,
            password=es_password,
        )

        # Dummy OB client for schema preview
        ob_client = None

        migrator = ESToOceanBaseMigrator(es_client, ob_client if ob_client else OBClient.__new__(OBClient))
        # Directly use schema converter
        from .schema import RAGFlowSchemaConverter
        converter = RAGFlowSchemaConverter()

        es_mapping = es_client.get_index_mapping(index)
        analysis = converter.analyze_es_mapping(es_mapping)
        column_defs = converter.get_column_definitions()

        # Display analysis
        console.print(f"\n[bold]ES Index Analysis: {index}[/]\n")

        # Known RAGFlow fields
        console.print(f"[green]Known RAGFlow fields:[/] {len(analysis['known_fields'])}")

        # Vector fields
        if analysis['vector_fields']:
            console.print("\n[cyan]Vector fields detected:[/]")
            for vf in analysis['vector_fields']:
                console.print(f"  - {vf['name']} (dimension: {vf['dimension']})")

        # Unknown fields
        if analysis['unknown_fields']:
            console.print("\n[yellow]Unknown fields (will be stored in 'extra'):[/]")
            for uf in analysis['unknown_fields']:
                console.print(f"  - {uf}")

        # Display RAGFlow column schema
        console.print(f"\n[bold]RAGFlow OceanBase Schema ({len(column_defs)} columns):[/]\n")

        table = Table(title="Column Definitions")
        table.add_column("Column Name", style="cyan")
        table.add_column("OB Type", style="green")
        table.add_column("Nullable", style="yellow")
        table.add_column("Special", style="magenta")

        for col in column_defs[:20]:  # Show first 20
            special = []
            if col.get("is_primary"):
                special.append("PK")
            if col.get("index"):
                special.append("IDX")
            if col.get("is_array"):
                special.append("ARRAY")
            if col.get("is_vector"):
                special.append("VECTOR")

            table.add_row(
                col["name"],
                col["ob_type"],
                "Yes" if col.get("nullable", True) else "No",
                ", ".join(special) if special else "-",
            )

        if len(column_defs) > 20:
            table.add_row("...", f"({len(column_defs) - 20} more)", "", "")

        console.print(table)

        # Save to file if requested
        if output:
            preview = {
                "es_index": index,
                "es_mapping": es_mapping,
                "analysis": analysis,
                "ob_columns": column_defs,
            }
            with open(output, "w") as f:
                json.dump(preview, f, indent=2, default=str)
            console.print(f"\nSchema saved to {output}")

    except Exception as e:
        console.print(f"[bold red]Error: {e}[/]")
        if ctx.obj.get("verbose"):
            console.print_exception()
        sys.exit(1)
    finally:
        if "es_client" in locals():
            es_client.close()