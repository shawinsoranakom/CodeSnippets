def get_expected_values(self, image_inputs, batched=False):
        if not batched:
            shortest_edge = self.size["shortest_edge"]
            longest_edge = self.size["longest_edge"]
            image = image_inputs[0]
            if isinstance(image, Image.Image):
                w, h = image.size
            elif isinstance(image, np.ndarray):
                h, w = image.shape[0], image.shape[1]
            else:
                h, w = image.shape[1], image.shape[2]

            aspect_ratio = w / h
            if w > h and w >= longest_edge:
                w = longest_edge
                h = int(w / aspect_ratio)
            elif h > w and h >= longest_edge:
                h = longest_edge
                w = int(h * aspect_ratio)
            w = max(w, shortest_edge)
            h = max(h, shortest_edge)
            expected_height = h
            expected_width = w
        else:
            expected_values = []
            for images in image_inputs:
                for image in images:
                    expected_height, expected_width = self.get_expected_values([image])
                    expected_values.append((expected_height, expected_width))
            expected_height = max(expected_values, key=lambda item: item[0])[0]
            expected_width = max(expected_values, key=lambda item: item[1])[1]

        return expected_height, expected_width