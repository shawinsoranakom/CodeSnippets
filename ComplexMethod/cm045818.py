def predict(self, input_img):
        rotate_label = "0"  # Default to 0 if no rotation detected or not portrait
        if isinstance(input_img, Image.Image):
            np_img = np.asarray(input_img)
        elif isinstance(input_img, np.ndarray):
            np_img = input_img
        else:
            raise ValueError("Input must be a pillow object or a numpy array.")
        bgr_image = cv2.cvtColor(np_img, cv2.COLOR_RGB2BGR)
        # First check the overall image aspect ratio (height/width)
        img_height, img_width = bgr_image.shape[:2]
        img_aspect_ratio = img_height / img_width if img_width > 0 else 1.0
        img_is_portrait = img_aspect_ratio > 1.2

        if img_is_portrait:

            det_res = self.ocr_engine.ocr(bgr_image, rec=False)[0]
            # Check if table is rotated by analyzing text box aspect ratios
            if det_res:
                vertical_count = 0
                is_rotated = False

                for box_ocr_res in det_res:
                    p1, p2, p3, p4 = box_ocr_res

                    # Calculate width and height
                    width = p3[0] - p1[0]
                    height = p3[1] - p1[1]

                    aspect_ratio = width / height if height > 0 else 1.0

                    # Count vertical vs horizontal text boxes
                    if aspect_ratio < 0.8:  # Taller than wide - vertical text
                        vertical_count += 1
                    # elif aspect_ratio > 1.2:  # Wider than tall - horizontal text
                    #     horizontal_count += 1

                if vertical_count >= len(det_res) * 0.28 and vertical_count >= 3:
                    is_rotated = True
                # logger.debug(f"Text orientation analysis: vertical={vertical_count}, det_res={len(det_res)}, rotated={is_rotated}")

                # If we have more vertical text boxes than horizontal ones,
                # and vertical ones are significant, table might be rotated
                if is_rotated:
                    x = self.preprocess(np_img)
                    (result,) = self.sess.run(None, {"x": x})
                    rotate_label = self.labels[np.argmax(result)]
                    # logger.debug(f"Orientation classification result: {label}")

        return rotate_label