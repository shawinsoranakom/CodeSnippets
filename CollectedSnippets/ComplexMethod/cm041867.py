def take_screenshot_to_pil(screen=0, combine_screens=True):
    # Get information about all screens
    monitors = screeninfo.get_monitors()
    if screen == -1:  # All screens
        # Take a screenshot of each screen and save them in a list
        screenshots = [
            pyautogui.screenshot(
                region=(monitor.x, monitor.y, monitor.width, monitor.height)
            )
            for monitor in monitors
        ]

        if combine_screens:
            # Combine all screenshots horizontally
            total_width = sum([img.width for img in screenshots])
            max_height = max([img.height for img in screenshots])

            # Create a new image with a size that can contain all screenshots
            new_img = Image.new("RGB", (total_width, max_height))

            # Paste each screenshot into the new image
            x_offset = 0
            for i, img in enumerate(screenshots):
                # Convert PIL Image to OpenCV Image (numpy array)
                img_cv = np.array(img)
                img_cv = cv2.cvtColor(img_cv, cv2.COLOR_RGB2BGR)

                # Convert new_img PIL Image to OpenCV Image (numpy array)
                new_img_cv = np.array(new_img)
                new_img_cv = cv2.cvtColor(new_img_cv, cv2.COLOR_RGB2BGR)

                # Paste each screenshot into the new image using OpenCV
                new_img_cv[
                    0 : img_cv.shape[0], x_offset : x_offset + img_cv.shape[1]
                ] = img_cv
                x_offset += img.width

                # Add monitor labels using OpenCV
                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 4
                font_color = (255, 255, 255)
                line_type = 2

                if i == 0:
                    text = "Primary Monitor"
                else:
                    text = f"Monitor {i}"

                # Calculate the font scale that will fit the text perfectly in the center of the monitor
                text_size = cv2.getTextSize(text, font, font_scale, line_type)[0]
                font_scale = min(img.width / text_size[0], img.height / text_size[1])

                # Recalculate the text size with the new font scale
                text_size = cv2.getTextSize(text, font, font_scale, line_type)[0]

                # Calculate the position to center the text
                text_x = x_offset - img.width // 2 - text_size[0] // 2
                text_y = max_height // 2 - text_size[1] // 2

                cv2.putText(
                    new_img_cv,
                    text,
                    (text_x, text_y),
                    font,
                    font_scale,
                    font_color,
                    line_type,
                )

                # Convert new_img from OpenCV Image back to PIL Image
                new_img_cv = cv2.cvtColor(new_img_cv, cv2.COLOR_BGR2RGB)
                new_img = Image.fromarray(new_img_cv)

            return new_img
        else:
            return screenshots
    elif screen > 0:
        # Take a screenshot of the selected screen
        return pyautogui.screenshot(
            region=(
                monitors[screen].x,
                monitors[screen].y,
                monitors[screen].width,
                monitors[screen].height,
            )
        )

    else:
        # Take a screenshot of the primary screen
        return pyautogui.screenshot(
            region=(
                monitors[screen].x,
                monitors[screen].y,
                monitors[screen].width,
                monitors[screen].height,
            )
        )