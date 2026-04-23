def get_element_boxes(image_data, debug):
    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
    debug_path = os.path.join(desktop_path, "oi-debug")

    if debug:
        if not os.path.exists(debug_path):
            os.makedirs(debug_path)

    # Re-import the original image for contrast adjustment
    # original_image = cv2.imread(image_path)

    # Convert the image to a format that PIL can work with
    # pil_image = Image.fromarray(cv2.cvtColor(original_image, cv2.COLOR_BGR2RGB))

    pil_image = image_data

    # Convert to grayscale
    pil_image = pil_image.convert("L")

    def process_image(
        pil_image,
        contrast_level=1.8,
        debug=False,
        debug_path=None,
        adaptive_method=cv2.ADAPTIVE_THRESH_MEAN_C,
        threshold_type=cv2.THRESH_BINARY_INV,
        block_size=11,
        C=3,
    ):
        # Apply an extreme contrast filter
        enhancer = ImageEnhance.Contrast(pil_image)
        contrasted_image = enhancer.enhance(
            contrast_level
        )  # Significantly increase contrast

        # Create a string with all parameters
        parameters_string = f"contrast_level_{contrast_level}-adaptive_method_{adaptive_method}-threshold_type_{threshold_type}-block_size_{block_size}-C_{C}"

        if debug:
            print("TRYING:", parameters_string)
            contrasted_image_path = os.path.join(
                debug_path, f"contrasted_image_{parameters_string}.jpg"
            )
            contrasted_image.save(contrasted_image_path)
            print(f"DEBUG: Contrasted image saved to {contrasted_image_path}")

        # Convert the contrast-enhanced image to OpenCV format
        contrasted_image_cv = cv2.cvtColor(
            np.array(contrasted_image), cv2.COLOR_RGB2BGR
        )

        # Convert the contrast-enhanced image to grayscale
        gray_contrasted = cv2.cvtColor(contrasted_image_cv, cv2.COLOR_BGR2GRAY)
        if debug:
            image_path = os.path.join(
                debug_path, f"gray_contrasted_image_{parameters_string}.jpg"
            )
            cv2.imwrite(image_path, gray_contrasted)
            print("DEBUG: Grayscale contrasted image saved at:", image_path)

        # Apply adaptive thresholding to create a binary image where the GUI elements are isolated
        binary_contrasted = cv2.adaptiveThreshold(
            src=gray_contrasted,
            maxValue=255,
            adaptiveMethod=adaptive_method,
            thresholdType=threshold_type,
            blockSize=block_size,
            C=C,
        )

        if debug:
            binary_contrasted_image_path = os.path.join(
                debug_path, f"binary_contrasted_image_{parameters_string}.jpg"
            )
            cv2.imwrite(binary_contrasted_image_path, binary_contrasted)
            print(
                f"DEBUG: Binary contrasted image saved to {binary_contrasted_image_path}"
            )

        # Find contours from the binary image
        contours_contrasted, _ = cv2.findContours(
            binary_contrasted, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE
        )

        # Optionally, draw contours on the image for visualization
        contour_image = np.zeros_like(binary_contrasted)
        cv2.drawContours(contour_image, contours_contrasted, -1, (255, 255, 255), 1)

        if debug:
            contoured_contrasted_image_path = os.path.join(
                debug_path, f"contoured_contrasted_image_{parameters_string}.jpg"
            )
            cv2.imwrite(contoured_contrasted_image_path, contour_image)
            print(
                f"DEBUG: Contoured contrasted image saved at: {contoured_contrasted_image_path}"
            )

        return contours_contrasted

    if os.getenv("OI_POINT_PERMUTATE", "False") == "True":
        import random

        for _ in range(10):
            random_contrast = random.uniform(
                1, 40
            )  # Random contrast in range 0.5 to 1.5
            random_block_size = random.choice(
                range(1, 11, 2)
            )  # Random block size in range 1 to 10, but only odd numbers
            random_block_size = 11
            random_adaptive_method = random.choice(
                [cv2.ADAPTIVE_THRESH_MEAN_C, cv2.ADAPTIVE_THRESH_GAUSSIAN_C]
            )  # Random adaptive method
            random_threshold_type = random.choice(
                [cv2.THRESH_BINARY, cv2.THRESH_BINARY_INV]
            )  # Random threshold type
            random_C = random.randint(-10, 10)  # Random C in range 1 to 10
            contours_contrasted = process_image(
                pil_image,
                contrast_level=random_contrast,
                block_size=random_block_size,
                adaptive_method=random_adaptive_method,
                threshold_type=random_threshold_type,
                C=random_C,
                debug=debug,
                debug_path=debug_path,
            )

        print("Random Contrast: ", random_contrast)
        print("Random Block Size: ", random_block_size)
        print("Random Adaptive Method: ", random_adaptive_method)
        print("Random Threshold Type: ", random_threshold_type)
        print("Random C: ", random_C)
    else:
        contours_contrasted = process_image(
            pil_image, debug=debug, debug_path=debug_path
        )

    if debug:
        print("WE HERE")

    # Initialize an empty list to store the boxes
    boxes = []
    for contour in contours_contrasted:
        # Get the rectangle that bounds the contour
        x, y, w, h = cv2.boundingRect(contour)
        # Append the box as a dictionary to the list
        boxes.append({"x": x, "y": y, "width": w, "height": h})

    if debug:
        print("WE HHERE")

    if (
        False
    ):  # Disabled. I thought this would be faster but it's actually slower than just embedding all of them.
        # Remove any boxes whose edges cross over any contours
        filtered_boxes = []
        for box in boxes:
            crosses_contour = False
            for contour in contours_contrasted:
                if (
                    cv2.pointPolygonTest(contour, (box["x"], box["y"]), False) >= 0
                    or cv2.pointPolygonTest(
                        contour, (box["x"] + box["width"], box["y"]), False
                    )
                    >= 0
                    or cv2.pointPolygonTest(
                        contour, (box["x"], box["y"] + box["height"]), False
                    )
                    >= 0
                    or cv2.pointPolygonTest(
                        contour,
                        (box["x"] + box["width"], box["y"] + box["height"]),
                        False,
                    )
                    >= 0
                ):
                    crosses_contour = True
                    break
            if not crosses_contour:
                filtered_boxes.append(box)
        boxes = filtered_boxes

    if debug:
        print("WE HHHERE")

    return boxes