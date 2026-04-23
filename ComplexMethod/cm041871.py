def image_search(query, icons, hashes, debug):
    hashed_icons = [icon for icon in icons if icon["hash"] in hashes]
    unhashed_icons = [icon for icon in icons if icon["hash"] not in hashes]

    # Embed the unhashed icons
    if fast_model:
        query_and_unhashed_icons_embeds = model.encode(
            [query] + [icon["data"] for icon in unhashed_icons],
            batch_size=128,
            convert_to_tensor=True,
            show_progress_bar=debug,
        )
    else:
        query_and_unhashed_icons_embeds = embed_images(
            [query] + [icon["data"] for icon in unhashed_icons], model, transforms
        )

    query_embed = query_and_unhashed_icons_embeds[0]
    unhashed_icons_embeds = query_and_unhashed_icons_embeds[1:]

    # Store hashes for unhashed icons
    for icon, emb in zip(unhashed_icons, unhashed_icons_embeds):
        hashes[icon["hash"]] = emb

    # Move tensors to the specified device before concatenating
    unhashed_icons_embeds = unhashed_icons_embeds.to(device)

    # Include hashed icons in img_emb
    img_emb = torch.cat(
        [unhashed_icons_embeds]
        + [hashes[icon["hash"]].unsqueeze(0) for icon in hashed_icons]
    )

    # Perform semantic search
    hits = util.semantic_search(query_embed, img_emb)[0]

    # Filter hits with score over 90
    results = [hit for hit in hits if hit["score"] > 90]

    # Ensure top result is included
    if hits and (hits[0] not in results):
        results.insert(0, hits[0])

    # Convert results to original icon format
    return [icons[hit["corpus_id"]] for hit in results]