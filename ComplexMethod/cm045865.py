def prepare_input(self, img, random_padding: bool = False):
        """
        Convert PIL Image or numpy array to properly sized and padded image after:
            - crop margins
            - resize while maintaining aspect ratio
            - pad to target size
        """
        if img is None:
            return None

        # Handle numpy array
        elif isinstance(img, np.ndarray):
            try:
                img = self.crop_margin_numpy(img)
            except Exception:
                # might throw an error for broken files
                return None

            if img.shape[0] == 0 or img.shape[1] == 0:
                return None

            # Get current dimensions
            h, w = img.shape[:2]
            target_h, target_w = self.input_size

            # Calculate scale to preserve aspect ratio (equivalent to resize + thumbnail)
            scale = min(target_h / h, target_w / w)

            # Calculate new dimensions
            new_h, new_w = int(h * scale), int(w * scale)

            # Resize the image while preserving aspect ratio
            resized_img = cv2.resize(img, (new_w, new_h))

            # Calculate padding values using the existing method
            delta_width = target_w - new_w
            delta_height = target_h - new_h

            pad_width, pad_height = self._get_padding_values(new_w, new_h, random_padding)

            # Apply padding (convert PIL padding format to OpenCV format)
            padding_color = [0, 0, 0] if len(img.shape) == 3 else [0]

            padded_img = cv2.copyMakeBorder(
                resized_img,
                pad_height,  # top
                delta_height - pad_height,  # bottom
                pad_width,  # left
                delta_width - pad_width,  # right
                cv2.BORDER_CONSTANT,
                value=padding_color
            )

            return padded_img

        # Handle PIL Image
        elif isinstance(img, Image.Image):
            try:
                img = self.crop_margin(img.convert("RGB"))
            except OSError:
                # might throw an error for broken files
                return None

            if img.height == 0 or img.width == 0:
                return None

            # Resize while preserving aspect ratio
            img = resize(img, min(self.input_size))
            img.thumbnail((self.input_size[1], self.input_size[0]))
            new_w, new_h = img.width, img.height

            # Calculate and apply padding
            padding = self._calculate_padding(new_w, new_h, random_padding)
            return np.array(ImageOps.expand(img, padding))

        else:
            return None