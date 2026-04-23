def screenshot(
        self,
        screen=0,
        show=True,
        quadrant=None,
        active_app_only=True,
        combine_screens=True,
    ):
        """
        Shows you what's on the screen by taking a screenshot of the entire screen or a specified quadrant. Returns a `pil_image` `in case you need it (rarely). **You almost always want to do this first!**
        :param screen: specify which display; 0 for primary and 1 and above for secondary.
        :param combine_screens: If True, a collage of all display screens will be returned. Otherwise, a list of display screens will be returned.
        """

        # Since Local II, all images sent to local models will be rendered to text with moondream and pytesseract.
        # So we don't need to do this here— we can just emit images.
        # We should probably remove self.computer.emit_images for this reason.

        # if not self.computer.emit_images and force_image == False:
        #     screenshot = self.screenshot(show=False, force_image=True)

        #     description = self.computer.vision.query(pil_image=screenshot)
        #     print("A DESCRIPTION OF WHAT'S ON THE SCREEN: " + description)

        #     if self.computer.max_output > 600:
        #         print("ALL OF THE TEXT ON THE SCREEN: ")
        #         text = self.get_text_as_list_of_lists(screenshot=screenshot)
        #         pp = pprint.PrettyPrinter(indent=4)
        #         pretty_text = pp.pformat(text)  # language models like it pretty!
        #         pretty_text = format_to_recipient(pretty_text, "assistant")
        #         print(pretty_text)
        #         print(
        #             format_to_recipient(
        #                 "To receive the text above as a Python object, run computer.display.get_text_as_list_of_lists()",
        #                 "assistant",
        #             )
        #         )
        #     return screenshot  # Still return a PIL image

        if quadrant == None:
            if active_app_only:
                active_window = pywinctl.getActiveWindow()
                if active_window:
                    screenshot = pyautogui.screenshot(
                        region=(
                            active_window.left,
                            active_window.top,
                            active_window.width,
                            active_window.height,
                        )
                    )
                    message = format_to_recipient(
                        "Taking a screenshot of the active app. To take a screenshot of the entire screen (uncommon), use computer.view(active_app_only=False).",
                        "assistant",
                    )
                    print(message)
                else:
                    screenshot = pyautogui.screenshot()

            else:
                screenshot = take_screenshot_to_pil(
                    screen=screen, combine_screens=combine_screens
                )  #  this function uses pyautogui.screenshot which works fine for all OS (mac, linux and windows)
                message = format_to_recipient(
                    "Taking a screenshot of the entire screen.\n\nTo focus on the active app, use computer.display.view(active_app_only=True).",
                    "assistant",
                )
                print(message)

        else:
            screen_width, screen_height = pyautogui.size()

            quadrant_width = screen_width // 2
            quadrant_height = screen_height // 2

            quadrant_coordinates = {
                1: (0, 0),
                2: (quadrant_width, 0),
                3: (0, quadrant_height),
                4: (quadrant_width, quadrant_height),
            }

            if quadrant in quadrant_coordinates:
                x, y = quadrant_coordinates[quadrant]
                screenshot = pyautogui.screenshot(
                    region=(x, y, quadrant_width, quadrant_height)
                )
            else:
                raise ValueError("Invalid quadrant. Choose between 1 and 4.")

        # Open the image file with PIL
        # IPython interactive mode auto-displays plots, causing RGBA handling issues, possibly MacOS-specific.
        if isinstance(screenshot, list):
            screenshot = [
                img.convert("RGB") for img in screenshot
            ]  # if screenshot is a list (i.e combine_screens=False).
        else:
            screenshot = screenshot.convert("RGB")

        if show:
            # Show the image using IPython display
            if isinstance(screenshot, list):
                for img in screenshot:
                    display(img)
            else:
                display(screenshot)

        return screenshot