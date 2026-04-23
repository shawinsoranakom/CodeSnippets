def _extract_images_from_page(page: Any) -> list[dict]:
    """
    Extract images from a PDF page by rendering page regions.

    Returns:
        List of dicts with 'stream', 'bbox', 'name', 'y_pos' keys
    """
    images_info = []

    try:
        # Try multiple methods to detect images
        images = []

        # Method 1: Use page.images (standard approach)
        if hasattr(page, "images") and page.images:
            images = page.images

        # Method 2: If no images found, try underlying PDF objects
        if not images and hasattr(page, "objects") and "image" in page.objects:
            images = page.objects.get("image", [])

        # Method 3: Try filtering all objects for image types
        if not images and hasattr(page, "objects"):
            all_objs = page.objects
            for obj_type in all_objs.keys():
                if "image" in obj_type.lower() or "xobject" in obj_type.lower():
                    potential_imgs = all_objs.get(obj_type, [])
                    if potential_imgs:
                        images = potential_imgs
                        break

        for i, img_dict in enumerate(images):
            try:
                # Try to get the actual image stream from the PDF
                img_stream = None
                y_pos = 0

                # Method A: If img_dict has 'stream' key, use it directly
                if "stream" in img_dict and hasattr(img_dict["stream"], "get_data"):
                    try:
                        img_bytes = img_dict["stream"].get_data()

                        # Try to open as PIL Image to validate/decode
                        pil_img = Image.open(io.BytesIO(img_bytes))

                        # Convert to RGB if needed (handle CMYK, etc.)
                        if pil_img.mode not in ("RGB", "L"):
                            pil_img = pil_img.convert("RGB")

                        # Save to stream as PNG
                        img_stream = io.BytesIO()
                        pil_img.save(img_stream, format="PNG")
                        img_stream.seek(0)

                        y_pos = img_dict.get("top", 0)
                    except Exception:
                        pass

                # Method B: Fallback to rendering page region
                if img_stream is None:
                    x0 = img_dict.get("x0", 0)
                    y0 = img_dict.get("top", 0)
                    x1 = img_dict.get("x1", 0)
                    y1 = img_dict.get("bottom", 0)
                    y_pos = y0

                    # Check if dimensions are valid
                    if x1 <= x0 or y1 <= y0:
                        continue

                    # Use pdfplumber's within_bbox to crop, then render
                    # This preserves coordinate system correctly
                    bbox = (x0, y0, x1, y1)
                    cropped_page = page.within_bbox(bbox)

                    # Render at 150 DPI (balance between quality and size)
                    page_img = cropped_page.to_image(resolution=150)

                    # Save to stream
                    img_stream = io.BytesIO()
                    page_img.original.save(img_stream, format="PNG")
                    img_stream.seek(0)

                if img_stream:
                    images_info.append(
                        {
                            "stream": img_stream,
                            "name": f"page_{page.page_number}_img_{i}",
                            "y_pos": y_pos,
                        }
                    )

            except Exception:
                continue

    except Exception:
        pass

    return images_info