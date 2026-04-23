def find_icon(description, screenshot=None, debug=False, hashes=None):
    if debug:
        print("STARTING")
    if screenshot == None:
        image_data = take_screenshot_to_pil()
    else:
        image_data = screenshot

    if hashes == None:
        hashes = {}

    image_width, image_height = image_data.size

    # Create a temporary file to save the image data
    #   with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
    #     temp_file.write(base64.b64decode(request.base64))
    #     temp_image_path = temp_file.name
    #   print("yeah took", time.time()-thetime)

    icons_bounding_boxes = get_element_boxes(image_data, debug)

    if debug:
        print("GOT ICON BOUNDING BOXES")

    debug_path = os.path.join(os.path.expanduser("~"), "Desktop", "oi-debug")

    if debug:
        # Create a draw object
        image_data_copy = image_data.copy()
        draw = ImageDraw.Draw(image_data_copy)
        # Draw red rectangles around all blocks
        for block in icons_bounding_boxes:
            left, top, width, height = (
                block["x"],
                block["y"],
                block["width"],
                block["height"],
            )
            draw.rectangle([(left, top), (left + width, top + height)], outline="red")
        image_data_copy.save(
            os.path.join(debug_path, "before_filtering_out_extremes.png")
        )

    # Filter out extremes
    min_icon_width = int(os.getenv("OI_POINT_MIN_ICON_WIDTH", "10"))
    max_icon_width = int(os.getenv("OI_POINT_MAX_ICON_WIDTH", "500"))
    min_icon_height = int(os.getenv("OI_POINT_MIN_ICON_HEIGHT", "10"))
    max_icon_height = int(os.getenv("OI_POINT_MAX_ICON_HEIGHT", "500"))
    icons_bounding_boxes = [
        box
        for box in icons_bounding_boxes
        if min_icon_width <= box["width"] <= max_icon_width
        and min_icon_height <= box["height"] <= max_icon_height
    ]

    if debug:
        # Create a draw object
        image_data_copy = image_data.copy()
        draw = ImageDraw.Draw(image_data_copy)
        # Draw red rectangles around all blocks
        for block in icons_bounding_boxes:
            left, top, width, height = (
                block["x"],
                block["y"],
                block["width"],
                block["height"],
            )
            draw.rectangle([(left, top), (left + width, top + height)], outline="red")
        image_data_copy.save(
            os.path.join(debug_path, "after_filtering_out_extremes.png")
        )

    # Compute center_x and center_y for each box
    for box in icons_bounding_boxes:
        box["center_x"] = box["x"] + box["width"] / 2
        box["center_y"] = box["y"] + box["height"] / 2

    # # Filter out text

    if debug:
        print("GETTING TEXT")

    response = pytesseract_get_text_bounding_boxes(screenshot)

    if debug:
        print("GOT TEXT, processing it")

    if debug:
        # Create a draw object
        image_data_copy = image_data.copy()
        draw = ImageDraw.Draw(image_data_copy)
        # Draw red rectangles around all blocks
        for block in response:
            left, top, width, height = (
                block["left"],
                block["top"],
                block["width"],
                block["height"],
            )
            draw.rectangle([(left, top), (left + width, top + height)], outline="blue")

        # Save the image to the desktop
        if not os.path.exists(debug_path):
            os.makedirs(debug_path)
        image_data_copy.save(os.path.join(debug_path, "pytesseract_blocks_image.png"))

    blocks = [
        b for b in response if len(b["text"]) > 2
    ]  # icons are sometimes text, like "X"

    # Filter blocks so the text.lower() needs to be a real word in the English dictionary
    filtered_blocks = []
    for b in blocks:
        words = b["text"].lower().split()
        words = [
            "".join(e for e in word if e.isalnum()) for word in words
        ]  # remove punctuation
        if all(word in english_words for word in words):
            filtered_blocks.append(b)
    blocks = filtered_blocks

    if debug:
        # Create a draw object
        image_data_copy = image_data.copy()
        draw = ImageDraw.Draw(image_data_copy)
        # Draw red rectangles around all blocks
        for block in blocks:
            left, top, width, height = (
                block["left"],
                block["top"],
                block["width"],
                block["height"],
            )
            draw.rectangle([(left, top), (left + width, top + height)], outline="green")
        image_data_copy.save(
            os.path.join(debug_path, "pytesseract_filtered_blocks_image.png")
        )

    if debug:
        # Create a draw object
        image_data_copy = image_data.copy()
        draw = ImageDraw.Draw(image_data_copy)
        # Draw red rectangles around all blocks
        for block in blocks:
            left, top, width, height = (
                block["left"],
                block["top"],
                block["width"],
                block["height"],
            )
            draw.rectangle([(left, top), (left + width, top + height)], outline="green")
            # Draw the detected text in the rectangle in small font
            # Use PIL's built-in bitmap font
            font = ImageFont.load_default()
            draw.text(
                (block["left"], block["top"]), block["text"], fill="red", font=font
            )
        image_data_copy.save(
            os.path.join(debug_path, "pytesseract_filtered_blocks_image_with_text.png")
        )

    # Create an empty list to store the filtered boxes
    filtered_boxes = []

    # Filter out boxes that fall inside text
    for box in icons_bounding_boxes:
        if not any(
            text_box["left"] <= box["x"] <= text_box["left"] + text_box["width"]
            and text_box["top"] <= box["y"] <= text_box["top"] + text_box["height"]
            and text_box["left"]
            <= box["x"] + box["width"]
            <= text_box["left"] + text_box["width"]
            and text_box["top"]
            <= box["y"] + box["height"]
            <= text_box["top"] + text_box["height"]
            for text_box in blocks
        ):
            filtered_boxes.append(box)
        else:
            pass
            # print("Filtered out an icon because I think it is text.")

    icons_bounding_boxes = filtered_boxes

    if debug:
        # Create a copy of the image data
        image_data_copy = image_data.copy()
        draw = ImageDraw.Draw(image_data_copy)
        # Draw green rectangles around all filtered boxes
        for box in filtered_boxes:
            left, top, width, height = (
                box["x"],
                box["y"],
                box["width"],
                box["height"],
            )
            draw.rectangle([(left, top), (left + width, top + height)], outline="green")
        # Save the image with the drawn rectangles
        image_data_copy.save(
            os.path.join(debug_path, "pytesseract_filtered_boxes_image.png")
        )

    # Filter out boxes that intersect with text at all
    filtered_boxes = []
    for box in icons_bounding_boxes:
        if not any(
            max(text_box["left"], box["x"])
            < min(text_box["left"] + text_box["width"], box["x"] + box["width"])
            and max(text_box["top"], box["y"])
            < min(text_box["top"] + text_box["height"], box["y"] + box["height"])
            for text_box in blocks
        ):
            filtered_boxes.append(box)
    icons_bounding_boxes = filtered_boxes

    if debug:
        # Create a copy of the image data
        image_data_copy = image_data.copy()
        draw = ImageDraw.Draw(image_data_copy)
        # Draw green rectangles around all filtered boxes
        for box in icons_bounding_boxes:
            left, top, width, height = (
                box["x"],
                box["y"],
                box["width"],
                box["height"],
            )
            draw.rectangle([(left, top), (left + width, top + height)], outline="green")
        # Save the image with the drawn rectangles
        image_data_copy.save(
            os.path.join(debug_path, "debug_image_after_filtering_boxes.png")
        )

    # # (DISABLED)
    # # Filter to the most icon-like dimensions

    # # Desired dimensions
    # desired_width = 30
    # desired_height = 30

    # # Calculating the distance of each box's dimensions from the desired dimensions
    # for box in icons_bounding_boxes:
    #     width_diff = abs(box["width"] - desired_width)
    #     height_diff = abs(box["height"] - desired_height)
    #     # Sum of absolute differences as a simple measure of "closeness"
    #     box["distance"] = width_diff + height_diff

    # # Sorting the boxes based on their closeness to the desired dimensions
    # sorted_boxes = sorted(icons_bounding_boxes, key=lambda x: x["distance"])

    # # Selecting the top 150 closest boxes
    # icons_bounding_boxes = sorted_boxes  # DISABLED [:150]

    # Expand a little

    # Define the pixel expansion amount
    pixel_expand = int(os.getenv("OI_POINT_PIXEL_EXPAND", 7))

    # Expand each box by pixel_expand
    for box in icons_bounding_boxes:
        # Expand x, y by pixel_expand if they are greater than 0
        box["x"] = box["x"] - pixel_expand if box["x"] - pixel_expand >= 0 else box["x"]
        box["y"] = box["y"] - pixel_expand if box["y"] - pixel_expand >= 0 else box["y"]

        # Expand w, h by pixel_expand, but not beyond image_width and image_height
        box["width"] = (
            box["width"] + pixel_expand * 2
            if box["x"] + box["width"] + pixel_expand * 2 <= image_width
            else image_width - box["x"] - box["width"]
        )
        box["height"] = (
            box["height"] + pixel_expand * 2
            if box["y"] + box["height"] + pixel_expand * 2 <= image_height
            else image_height - box["y"] - box["height"]
        )

    # Save a debug image with a descriptive name for the step we just went through
    if debug:
        image_data_copy = image_data.copy()
        draw = ImageDraw.Draw(image_data_copy)
        for box in icons_bounding_boxes:
            left = box["x"]
            top = box["y"]
            width = box["width"]
            height = box["height"]
            draw.rectangle([(left, top), (left + width, top + height)], outline="red")
        image_data_copy.save(
            os.path.join(debug_path, "debug_image_after_expanding_boxes.png")
        )

    def combine_boxes(icons_bounding_boxes):
        while True:
            combined_boxes = []
            for box in icons_bounding_boxes:
                for i, combined_box in enumerate(combined_boxes):
                    if (
                        box["x"] < combined_box["x"] + combined_box["width"]
                        and box["x"] + box["width"] > combined_box["x"]
                        and box["y"] < combined_box["y"] + combined_box["height"]
                        and box["y"] + box["height"] > combined_box["y"]
                    ):
                        combined_box["x"] = min(box["x"], combined_box["x"])
                        combined_box["y"] = min(box["y"], combined_box["y"])
                        combined_box["width"] = (
                            max(
                                box["x"] + box["width"],
                                combined_box["x"] + combined_box["width"],
                            )
                            - combined_box["x"]
                        )
                        combined_box["height"] = (
                            max(
                                box["y"] + box["height"],
                                combined_box["y"] + combined_box["height"],
                            )
                            - combined_box["y"]
                        )
                        break
                else:
                    combined_boxes.append(box.copy())
            if len(combined_boxes) == len(icons_bounding_boxes):
                break
            else:
                icons_bounding_boxes = combined_boxes
        return combined_boxes

    if os.getenv("OI_POINT_OVERLAP", "True") == "True":
        icons_bounding_boxes = combine_boxes(icons_bounding_boxes)

    if debug:
        image_data_copy = image_data.copy()
        draw = ImageDraw.Draw(image_data_copy)
        for box in icons_bounding_boxes:
            x, y, w, h = box["x"], box["y"], box["width"], box["height"]
            draw.rectangle([(x, y), (x + w, y + h)], outline="blue")
        image_data_copy.save(
            os.path.join(debug_path, "debug_image_after_combining_boxes.png")
        )

    icons = []
    for box in icons_bounding_boxes:
        x, y, w, h = box["x"], box["y"], box["width"], box["height"]

        icon_image = image_data.crop((x, y, x + w, y + h))

        # icon_image.show()
        # input("Press Enter to finish looking at the image...")

        icon = {}
        icon["data"] = icon_image
        icon["x"] = x
        icon["y"] = y
        icon["width"] = w
        icon["height"] = h

        icon_image_hash = hashlib.sha256(icon_image.tobytes()).hexdigest()
        icon["hash"] = icon_image_hash

        # Calculate the relative central xy coordinates of the bounding box
        center_x = box["center_x"] / image_width  # Relative X coordinate
        center_y = box["center_y"] / image_height  # Relative Y coordinate
        icon["coordinate"] = (center_x, center_y)

        icons.append(icon)

    # Draw and show an image with the full screenshot and all the icons bounding boxes drawn on it in red
    if debug:
        image_data_copy = image_data.copy()
        draw = ImageDraw.Draw(image_data_copy)
        for icon in icons:
            x, y, w, h = icon["x"], icon["y"], icon["width"], icon["height"]
            draw.rectangle([(x, y), (x + w, y + h)], outline="red")
        desktop = os.path.join(os.path.join(os.path.expanduser("~")), "Desktop")
        image_data_copy.save(os.path.join(desktop, "point_vision.png"))

    if "icon" not in description.lower():
        description += " icon"

    if debug:
        print("FINALLY, SEARCHING")

    top_icons = image_search(description, icons, hashes, debug)

    if debug:
        print("DONE")

    coordinates = [t["coordinate"] for t in top_icons]

    # Return the top pick icon data
    return coordinates