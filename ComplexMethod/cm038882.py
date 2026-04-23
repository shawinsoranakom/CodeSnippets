def main(args):
    pooling_url = f"http://{args.host}:{args.port}/pooling"
    score_url = f"http://{args.host}:{args.port}/score"
    model = args.model

    # Same sample data as the official TomoroAI example
    queries = [
        "Retrieve the city of Singapore",
        "Retrieve the city of Beijing",
        "Retrieve the city of London",
    ]
    image_urls = [
        "https://upload.wikimedia.org/wikipedia/commons/2/27/Singapore_skyline_2022.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/6/61/Beijing_skyline_at_night.JPG",
        "https://upload.wikimedia.org/wikipedia/commons/4/49/London_skyline.jpg",
    ]

    # ── 1) Text query embeddings ────────────────────────────
    print("=" * 60)
    print("1. Encode text queries (multi-vector)")
    print("=" * 60)
    query_embeddings = encode_queries(queries, model, pooling_url)
    for i, emb in enumerate(query_embeddings):
        norm = float(np.linalg.norm(emb[0]))
        print(f'  Query {i}: {emb.shape}  (L2 norm: {norm:.4f})  "{queries[i]}"')

    # ── 2) Image document embeddings ────────────────────────
    print()
    print("=" * 60)
    print("2. Encode image documents (multi-vector)")
    print("=" * 60)
    doc_embeddings = encode_images(image_urls, model, pooling_url)
    for i, emb in enumerate(doc_embeddings):
        print(f"  Doc {i}:   {emb.shape}  {image_urls[i].split('/')[-1]}")

    # ── 3) Cross-modal MaxSim scoring ───────────────────────
    if doc_embeddings:
        print()
        print("=" * 60)
        print("3. Cross-modal MaxSim scores (text queries × image docs)")
        print("=" * 60)
        # Header
        print(f"{'':>35s}", end="")
        for j in range(len(doc_embeddings)):
            print(f"  Doc {j:>2d}", end="")
        print()
        # Score matrix
        for i, q_emb in enumerate(query_embeddings):
            print(f"  {queries[i]:<33s}", end="")
            for j, d_emb in enumerate(doc_embeddings):
                score = compute_maxsim(q_emb, d_emb)
                print(f"  {score:6.2f}", end="")
            print()

    # ── 4) Text-only /score endpoint ────────────────────────
    print()
    print("=" * 60)
    print("4. Text-only late interaction scoring (/score endpoint)")
    print("=" * 60)
    text_query = "What is the capital of France?"
    text_docs = [
        "The capital of France is Paris.",
        "Berlin is the capital of Germany.",
        "Python is a programming language.",
    ]
    resp = post_http_request(
        {"model": model, "text_1": text_query, "text_2": text_docs},
        score_url,
    )
    print(f'  Query: "{text_query}"\n')
    for item in resp.json()["data"]:
        idx = item["index"]
        print(f"  Doc {idx} (score={item['score']:.4f}): {text_docs[idx]}")