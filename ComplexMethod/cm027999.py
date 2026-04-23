def download_and_embed_sample_images(_cohere_client) -> tuple[list[str], np.ndarray | None]:
    """Downloads sample images and computes their embeddings using Cohere's Embed-4 model."""
    # Several images from https://www.appeconomyinsights.com/
    images = {
        "tesla.png": "https://substackcdn.com/image/fetch/w_1456,c_limit,f_webp,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2Fbef936e6-3efa-43b3-88d7-7ec620cdb33b_2744x1539.png",
        "netflix.png": "https://substackcdn.com/image/fetch/w_1456,c_limit,f_webp,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F23bd84c9-5b62-4526-b467-3088e27e4193_2744x1539.png",
        "nike.png": "https://substackcdn.com/image/fetch/w_1456,c_limit,f_webp,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2Fa5cd33ba-ae1a-42a8-a254-d85e690d9870_2741x1541.png",
        "google.png": "https://substackcdn.com/image/fetch/f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F395dd3b9-b38e-4d1f-91bc-d37b642ee920_2741x1541.png",
        "accenture.png": "https://substackcdn.com/image/fetch/w_1456,c_limit,f_webp,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F08b2227c-7dc8-49f7-b3c5-13cab5443ba6_2741x1541.png",
        "tecent.png": "https://substackcdn.com/image/fetch/w_1456,c_limit,f_webp,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F0ec8448c-c4d1-4aab-a8e9-2ddebe0c95fd_2741x1541.png"
    }

    # Prepare folders
    img_folder = "img"
    os.makedirs(img_folder, exist_ok=True)

    img_paths = []
    doc_embeddings = []

    # Wrap TQDM with st.spinner for better UI integration
    with st.spinner("Downloading and embedding sample images..."):
        pbar = tqdm.tqdm(images.items(), desc="Processing sample images")
        for name, url in pbar:
            img_path = os.path.join(img_folder, name)
            # Don't re-append if already processed (useful if function called multiple times)
            if img_path not in img_paths:
                img_paths.append(img_path)

                # Download the image
                if not os.path.exists(img_path):
                    try:
                        response = requests.get(url)
                        response.raise_for_status()
                        with open(img_path, "wb") as fOut:
                            fOut.write(response.content)
                    except requests.exceptions.RequestException as e:
                        st.error(f"Failed to download {name}: {e}")
                        # Optionally remove the path if download failed
                        img_paths.pop()
                        continue # Skip if download fails

            # Get embedding for the image if it exists and we haven't computed one yet
            # Find index corresponding to this path
            current_index = -1
            try:
                current_index = img_paths.index(img_path)
            except ValueError:
                continue # Should not happen if append logic is correct

            # Check if embedding already exists for this index
            if current_index >= len(doc_embeddings):
                 try:
                     # Ensure file exists before trying to embed
                     if os.path.exists(img_path):
                         base64_img = base64_from_image(img_path)
                         emb = compute_image_embedding(base64_img, _cohere_client=_cohere_client)
                         if emb is not None:
                             # Placeholder to ensure list length matches paths before vstack
                             while len(doc_embeddings) < current_index:
                                 doc_embeddings.append(None) # Append placeholder if needed
                             doc_embeddings.append(emb)
                     else:
                         # If file doesn't exist (maybe failed download), add placeholder
                         while len(doc_embeddings) < current_index:
                                 doc_embeddings.append(None)
                         doc_embeddings.append(None)
                 except Exception as e:
                     st.error(f"Failed to embed {name}: {e}")
                     # Add placeholder on error
                     while len(doc_embeddings) < current_index:
                             doc_embeddings.append(None)
                     doc_embeddings.append(None)

    # Filter out None embeddings and corresponding paths before stacking
    filtered_paths = [path for i, path in enumerate(img_paths) if i < len(doc_embeddings) and doc_embeddings[i] is not None]
    filtered_embeddings = [emb for emb in doc_embeddings if emb is not None]

    if filtered_embeddings:
        doc_embeddings_array = np.vstack(filtered_embeddings)
        return filtered_paths, doc_embeddings_array

    return [], None