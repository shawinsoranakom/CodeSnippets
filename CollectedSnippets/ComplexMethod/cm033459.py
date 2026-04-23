def list_indices(ctx, es_host, es_port, es_user, es_password):
    """List all RAGFlow indices (ragflow_*) in Elasticsearch."""
    try:
        es_client = ESClient(
            host=es_host,
            port=es_port,
            username=es_user,
            password=es_password,
        )

        console.print(f"\n[bold]RAGFlow Indices in Elasticsearch ({es_host}:{es_port})[/]\n")

        indices = es_client.list_ragflow_indices()

        if not indices:
            console.print("[yellow]No ragflow_* indices found[/]")
            return

        table = Table(title="RAGFlow Indices")
        table.add_column("Index Name", style="cyan")
        table.add_column("Document Count", style="green", justify="right")
        table.add_column("Type", style="yellow")

        total_docs = 0
        for idx in indices:
            doc_count = es_client.count_documents(idx)
            total_docs += doc_count

            # Determine index type
            if idx.startswith("ragflow_doc_meta_"):
                idx_type = "Metadata"
            elif idx.startswith("ragflow_"):
                idx_type = "Document Chunks"
            else:
                idx_type = "Unknown"

            table.add_row(idx, f"{doc_count:,}", idx_type)

        table.add_row("", "", "")
        table.add_row("[bold]Total[/]", f"[bold]{total_docs:,}[/]", f"[bold]{len(indices)} indices[/]")

        console.print(table)

    except Exception as e:
        console.print(f"[bold red]Error: {e}[/]")
        if ctx.obj.get("verbose"):
            console.print_exception()
        sys.exit(1)
    finally:
        if "es_client" in locals():
            es_client.close()