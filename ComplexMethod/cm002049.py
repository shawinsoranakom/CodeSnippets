def test_padding(self):
        """
        LLaVA needs to pad images to square size before processing as per orig implementation.
        Checks that image processor pads images correctly given different background colors.
        """

        # taken from original implementation: https://github.com/haotian-liu/LLaVA/blob/c121f0432da27facab705978f83c4ada465e46fd/llava/mm_utils.py#L152
        def pad_to_square_original(
            image: Image.Image, background_color: int | tuple[int, int, int] = 0
        ) -> Image.Image:
            width, height = image.size
            if width == height:
                return image
            elif width > height:
                result = Image.new(image.mode, (width, width), background_color)
                result.paste(image, (0, (width - height) // 2))
                return result
            else:
                result = Image.new(image.mode, (height, height), background_color)
                result.paste(image, ((height - width) // 2, 0))
                return result

        for i, (backend_name, image_processing_class) in enumerate(self.image_processing_classes.items()):
            image_processor = image_processing_class.from_dict(self.image_processor_dict)
            numpify = backend_name == "pil"
            torchify = backend_name == "torchvision"
            image_inputs = self.image_processor_tester.prepare_image_inputs(
                equal_resolution=False, numpify=numpify, torchify=torchify
            )

            # test with images in channel-last and channel-first format (only channel-first for torch)
            for image in image_inputs:
                padded_image = image_processor.pad_to_square(
                    image.transpose(2, 0, 1) if backend_name == "pil" else image
                )
                if backend_name == "pil":
                    padded_image_original = pad_to_square_original(Image.fromarray(image))
                    padded_image_original = np.array(padded_image_original)
                    padded_image = padded_image.transpose(1, 2, 0)

                    np.testing.assert_allclose(padded_image, padded_image_original)
                else:
                    padded_image_original = pad_to_square_original(F.to_pil_image(image))
                    padded_image = padded_image.permute(1, 2, 0)
                    np.testing.assert_allclose(padded_image, padded_image_original)

            # test background color
            background_color = (122, 116, 104)
            for image in image_inputs:
                padded_image = image_processor.pad_to_square(
                    image.transpose(2, 0, 1) if backend_name == "pil" else image,
                    background_color=background_color,
                )
                if backend_name == "pil":
                    padded_image_original = pad_to_square_original(
                        Image.fromarray(image), background_color=background_color
                    )
                    padded_image = padded_image.transpose(1, 2, 0)
                else:
                    padded_image_original = pad_to_square_original(
                        F.to_pil_image(image), background_color=background_color
                    )
                    padded_image = padded_image.permute(1, 2, 0)
                padded_image_original = np.array(padded_image_original)

                np.testing.assert_allclose(padded_image, padded_image_original)

            background_color = 122
            for image in image_inputs:
                padded_image = image_processor.pad_to_square(
                    image.transpose(2, 0, 1) if backend_name == "pil" else image, background_color=background_color
                )
                if backend_name == "pil":
                    padded_image_original = pad_to_square_original(
                        Image.fromarray(image), background_color=background_color
                    )
                    padded_image = padded_image.transpose(1, 2, 0)
                else:
                    padded_image_original = pad_to_square_original(
                        F.to_pil_image(image), background_color=background_color
                    )
                    padded_image = padded_image.permute(1, 2, 0)
                padded_image_original = np.array(padded_image_original)
                np.testing.assert_allclose(padded_image, padded_image_original)

            # background color length should match channel length
            # torch shape is (C, H, W), numpy shape is (H, W, C)
            h_idx, w_idx = (1, 2) if torchify else (0, 1)
            if image_inputs[0].shape[h_idx] == image_inputs[0].shape[w_idx]:
                # This avoids a source of test flakiness - if the image is already square
                # no padding is done and background colour is not checked.
                continue

            with self.assertRaises(ValueError):
                padded_image = image_processor.pad_to_square(image_inputs[0], background_color=(122, 104))

            with self.assertRaises(ValueError):
                padded_image = image_processor.pad_to_square(image_inputs[0], background_color=(122, 104, 0, 0))