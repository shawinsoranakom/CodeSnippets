def process_pdf_file(pdf_file, cohere_client, base_output_folder="pdf_pages") -> tuple[list[str], list[np.ndarray] | None]:
    """Extracts pages from a PDF as images, embeds them, and saves them.

    Args:
        pdf_file: UploadedFile object from Streamlit.
        cohere_client: Initialized Cohere client.
        base_output_folder: Directory to save page images.

    Returns:
        A tuple containing: 
          - list of paths to the saved page images.
          - list of numpy array embeddings for each page, or None if embedding fails.
    """
    page_image_paths = []
    page_embeddings = []
    pdf_filename = pdf_file.name
    output_folder = os.path.join(base_output_folder, os.path.splitext(pdf_filename)[0])
    os.makedirs(output_folder, exist_ok=True)

    try:
        # Open PDF from stream
        doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
        st.write(f"Processing PDF: {pdf_filename} ({len(doc)} pages)")
        pdf_progress = st.progress(0.0)

        for i, page in enumerate(doc.pages()):
            page_num = i + 1
            page_img_path = os.path.join(output_folder, f"page_{page_num}.png")
            page_image_paths.append(page_img_path)

            # Render page to pixmap (image)
            pix = page.get_pixmap(dpi=150) # Adjust DPI as needed for quality/performance
            pil_image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

            # Save the page image temporarily
            pil_image.save(page_img_path, "PNG")

            # Convert PIL image to base64
            base64_img = pil_to_base64(pil_image)

            # Compute embedding for the page image
            emb = compute_image_embedding(base64_img, _cohere_client=cohere_client)
            if emb is not None:
                page_embeddings.append(emb)
            else:
                st.warning(f"Could not embed page {page_num} from {pdf_filename}. Skipping.")
                # Add a placeholder to keep lists aligned, will be filtered later
                page_embeddings.append(None)

            # Update progress
            pdf_progress.progress((i + 1) / len(doc))

        doc.close()
        pdf_progress.empty() # Remove progress bar after completion

        # Filter out pages where embedding failed
        valid_paths = [path for i, path in enumerate(page_image_paths) if page_embeddings[i] is not None]
        valid_embeddings = [emb for emb in page_embeddings if emb is not None]

        if not valid_embeddings:
             st.error(f"Failed to generate any embeddings for {pdf_filename}.")
             return [], None

        return valid_paths, valid_embeddings

    except Exception as e:
        st.error(f"Error processing PDF {pdf_filename}: {e}")
        return [], None