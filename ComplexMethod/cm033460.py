def sample(ctx, es_host, es_port, index, size):
    """Show sample documents from ES index."""
    try:
        es_client = ESClient(host=es_host, port=es_port)

        docs = es_client.get_sample_documents(index, size)

        console.print(f"\n[bold]Sample documents from {index}[/]")
        console.print()

        for i, doc in enumerate(docs, 1):
            console.print(f"[bold cyan]Document {i}[/]")
            console.print(f"  _id: {doc.get('_id')}")
            console.print(f"  kb_id: {doc.get('kb_id')}")
            console.print(f"  doc_id: {doc.get('doc_id')}")
            console.print(f"  docnm_kwd: {doc.get('docnm_kwd')}")

            # Check for vector fields
            vector_fields = [k for k in doc.keys() if k.startswith("q_") and k.endswith("_vec")]
            if vector_fields:
                for vf in vector_fields:
                    vec = doc.get(vf)
                    if vec:
                        console.print(f"  {vf}: [{len(vec)} dimensions]")

            content = doc.get("content_with_weight", "")
            if content:
                if isinstance(content, dict):
                    content = json.dumps(content, ensure_ascii=False)
                preview = content[:100] + "..." if len(str(content)) > 100 else content
                console.print(f"  content: {preview}")

            console.print()

        es_client.close()

    except Exception as e:
        console.print(f"[bold red]Error: {e}[/]")
        if ctx.obj.get("verbose"):
            console.print_exception()
        sys.exit(1)