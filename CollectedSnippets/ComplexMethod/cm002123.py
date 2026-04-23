def test_resize_image_and_array_non_default_to_square(self):
        feature_extractor = ImageFeatureExtractionMixin()

        heights_widths = [
            # height, width
            # square image
            (28, 28),
            (27, 27),
            # rectangular image: h < w
            (28, 34),
            (29, 35),
            # rectangular image: h > w
            (34, 28),
            (35, 29),
        ]

        # single integer or single integer in tuple/list
        sizes = [22, 27, 28, 36, [22], (27,)]

        for (height, width), size in zip(heights_widths, sizes):
            for max_size in (None, 37, 1000):
                image = get_random_image(height, width)
                array = np.array(image)

                size = size[0] if isinstance(size, (list, tuple)) else size
                # Size can be an int or a tuple of ints.
                # If size is an int, smaller edge of the image will be matched to this number.
                # i.e, if height > width, then image will be rescaled to (size * height / width, size).
                if height < width:
                    exp_w, exp_h = (int(size * width / height), size)
                    if max_size is not None and max_size < exp_w:
                        exp_w, exp_h = max_size, int(max_size * exp_h / exp_w)
                elif width < height:
                    exp_w, exp_h = (size, int(size * height / width))
                    if max_size is not None and max_size < exp_h:
                        exp_w, exp_h = int(max_size * exp_w / exp_h), max_size
                else:
                    exp_w, exp_h = (size, size)
                    if max_size is not None and max_size < size:
                        exp_w, exp_h = max_size, max_size

                resized_image = feature_extractor.resize(image, size=size, default_to_square=False, max_size=max_size)
                self.assertTrue(isinstance(resized_image, PIL.Image.Image))
                self.assertEqual(resized_image.size, (exp_w, exp_h))

                # Passing an array converts it to a PIL Image.
                resized_image2 = feature_extractor.resize(array, size=size, default_to_square=False, max_size=max_size)
                self.assertTrue(isinstance(resized_image2, PIL.Image.Image))
                self.assertEqual(resized_image2.size, (exp_w, exp_h))
                self.assertTrue(np.array_equal(np.array(resized_image), np.array(resized_image2)))