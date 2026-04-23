def test_small_model_pt(self):
        model_id = "hf-internal-testing/tiny-detr-mobilenetsv3-panoptic"

        model = AutoModelForImageSegmentation.from_pretrained(model_id)
        image_processor = AutoImageProcessor.from_pretrained(model_id)
        image_segmenter = ImageSegmentationPipeline(
            model=model,
            image_processor=image_processor,
            subtask="panoptic",
            threshold=0.0,
            mask_threshold=0.0,
            overlap_mask_area_threshold=0.0,
        )

        outputs = image_segmenter(
            "http://images.cocodataset.org/val2017/000000039769.jpg",
        )

        # Shortening by hashing
        for o in outputs:
            o["mask"] = mask_to_test_readable(o["mask"])

        # This is extremely brittle, and those values are made specific for the CI.
        self.assertEqual(
            nested_simplify(outputs, decimals=4),
            [
                {
                    "score": 0.004,
                    "label": "LABEL_215",
                    "mask": {"hash": "a01498ca7c", "shape": (480, 640), "white_pixels": 307200},
                },
            ],
        )

        outputs = image_segmenter(
            [
                "http://images.cocodataset.org/val2017/000000039769.jpg",
                "http://images.cocodataset.org/val2017/000000039769.jpg",
            ],
        )
        for output in outputs:
            for o in output:
                o["mask"] = mask_to_test_readable(o["mask"])

        self.assertEqual(
            nested_simplify(outputs, decimals=4),
            [
                [
                    {
                        "score": 0.004,
                        "label": "LABEL_215",
                        "mask": {"hash": "a01498ca7c", "shape": (480, 640), "white_pixels": 307200},
                    },
                ],
                [
                    {
                        "score": 0.004,
                        "label": "LABEL_215",
                        "mask": {"hash": "a01498ca7c", "shape": (480, 640), "white_pixels": 307200},
                    },
                ],
            ],
        )

        output = image_segmenter("http://images.cocodataset.org/val2017/000000039769.jpg", subtask="instance")
        for o in output:
            o["mask"] = mask_to_test_readable(o["mask"])
        self.assertEqual(
            nested_simplify(output, decimals=4),
            [
                {
                    "score": 0.004,
                    "label": "LABEL_215",
                    "mask": {"hash": "a01498ca7c", "shape": (480, 640), "white_pixels": 307200},
                },
            ],
        )

        # This must be surprising to the reader.
        # The `panoptic` returns only LABEL_215, and this returns 3 labels.
        #
        output = image_segmenter("http://images.cocodataset.org/val2017/000000039769.jpg", subtask="semantic")

        output_masks = [o["mask"] for o in output]

        # page links (to visualize)
        expected_masks = [
            "https://huggingface.co/datasets/hf-internal-testing/mask-for-image-segmentation-tests/blob/main/mask_0.png",
            "https://huggingface.co/datasets/hf-internal-testing/mask-for-image-segmentation-tests/blob/main/mask_1.png",
            "https://huggingface.co/datasets/hf-internal-testing/mask-for-image-segmentation-tests/blob/main/mask_2.png",
        ]
        # actual links to get files
        expected_masks = [x.replace("/blob/", "/resolve/") for x in expected_masks]
        expected_masks = [
            Image.open(io.BytesIO(httpx.get(image, follow_redirects=True).content)) for image in expected_masks
        ]

        # Convert masks to numpy array
        output_masks = [np.array(x) for x in output_masks]
        expected_masks = [np.array(x) for x in expected_masks]

        self.assertEqual(output_masks[0].shape, expected_masks[0].shape)
        self.assertEqual(output_masks[1].shape, expected_masks[1].shape)
        self.assertEqual(output_masks[2].shape, expected_masks[2].shape)

        # With un-trained tiny random models, the output `logits` tensor is very likely to contain many values
        # close to each other, which cause `argmax` to give quite different results when running the test on 2
        # environments. We use a lower threshold `0.9` here to avoid flakiness.
        self.assertGreaterEqual(np.mean(output_masks[0] == expected_masks[0]), 0.9)
        self.assertGreaterEqual(np.mean(output_masks[1] == expected_masks[1]), 0.9)
        self.assertGreaterEqual(np.mean(output_masks[2] == expected_masks[2]), 0.9)

        for o in output:
            o["mask"] = mask_to_test_readable_only_shape(o["mask"])
        self.maxDiff = None
        self.assertEqual(
            nested_simplify(output, decimals=4),
            [
                {
                    "label": "LABEL_88",
                    "mask": {"shape": (480, 640)},
                    "score": None,
                },
                {
                    "label": "LABEL_101",
                    "mask": {"shape": (480, 640)},
                    "score": None,
                },
                {
                    "label": "LABEL_215",
                    "mask": {"shape": (480, 640)},
                    "score": None,
                },
            ],
        )