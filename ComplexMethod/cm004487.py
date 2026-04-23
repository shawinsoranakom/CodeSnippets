def _fit_image_to_canvas(self, img_width: int, img_height: int, tile_size: int):
        """
        Given an image width, height and target number of chunks this function will see if the image
        can be fit into any of the canvases that can be build from arranging the tiles in a grid.
        If the image can be fit onto several canvases, it will return the canvas where the shorter edge
        of the image will be largest.
        """
        # Initialize the optimal canvas to None. If no canvas is found where image fits, function returns None.
        optimal_canvas = None
        optimal_image_width_height = None

        scale = img_width / img_height

        # Gather all potential supported image resolutions and iterate through them to find best match
        potential_arrangements = [
            item for sublist in self._find_supported_aspect_ratios().values() for item in sublist
        ]
        for n_w, n_h in potential_arrangements:
            # Compute the canvas size
            canvas_width, canvas_height = n_w * tile_size, n_h * tile_size

            # Check if image can fit into the canvas without downsampling
            if canvas_width >= img_width and canvas_height >= img_height:
                # If we did not find a good canvas yet, we will use the current one
                if optimal_canvas is None:
                    # Set optimal canvas and determine the actual image height and width in the canvas with aspect ratio preserving resampling
                    optimal_canvas = (n_w, n_h)
                    optimal_image_width_height = self._get_image_height_width(
                        image_width=img_width,
                        image_height=img_height,
                        target_width=n_w * tile_size,
                        target_height=n_h * tile_size,
                    )
                else:
                    # If we already found an optimal canvas before, we will check if the shorter edge of the image will be larger than the current optimal canvas.
                    # This means we can potentially upsample the image resolution which is beneficial to performance.
                    image_width_height = self._get_image_height_width(
                        image_width=img_width,
                        image_height=img_height,
                        target_width=n_w * tile_size,
                        target_height=n_h * tile_size,
                    )
                    # Llama3V dynamic tiling. Prioritize biggest canvas.
                    if (scale < 1.0 and (image_width_height[0] >= optimal_image_width_height[0])) or (
                        scale >= 1.0 and (image_width_height[1] >= optimal_image_width_height[1])
                    ):
                        optimal_canvas = (n_w, n_h)
                        optimal_image_width_height = image_width_height
        return optimal_canvas