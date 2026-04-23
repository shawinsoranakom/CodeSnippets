def test_chunk_iterator_stride(self):
        feature_extractor = AutoFeatureExtractor.from_pretrained("facebook/wav2vec2-base-960h")
        inputs = torch.arange(100).long()
        input_values = feature_extractor(inputs, sampling_rate=feature_extractor.sampling_rate, return_tensors="pt")[
            "input_values"
        ]
        outs = list(chunk_iter(inputs, feature_extractor, 100, 20, 10))
        self.assertEqual(len(outs), 1)
        self.assertEqual([o["stride"] for o in outs], [(100, 0, 0)])
        self.assertEqual([o["input_values"].shape for o in outs], [(1, 100)])
        self.assertEqual([o["is_last"] for o in outs], [True])

        outs = list(chunk_iter(inputs, feature_extractor, 80, 20, 10))
        self.assertEqual(len(outs), 2)
        self.assertEqual([o["stride"] for o in outs], [(80, 0, 10), (50, 20, 0)])
        self.assertEqual([o["input_values"].shape for o in outs], [(1, 80), (1, 50)])
        self.assertEqual([o["is_last"] for o in outs], [False, True])

        outs = list(chunk_iter(inputs, feature_extractor, 90, 20, 0))
        self.assertEqual(len(outs), 2)
        self.assertEqual([o["stride"] for o in outs], [(90, 0, 0), (30, 20, 0)])
        self.assertEqual([o["input_values"].shape for o in outs], [(1, 90), (1, 30)])

        outs = list(chunk_iter(inputs, feature_extractor, 36, 6, 6))
        self.assertEqual(len(outs), 4)
        self.assertEqual([o["stride"] for o in outs], [(36, 0, 6), (36, 6, 6), (36, 6, 6), (28, 6, 0)])
        self.assertEqual([o["input_values"].shape for o in outs], [(1, 36), (1, 36), (1, 36), (1, 28)])

        inputs = torch.LongTensor([i % 2 for i in range(100)])
        input_values = feature_extractor(inputs, sampling_rate=feature_extractor.sampling_rate, return_tensors="pt")[
            "input_values"
        ]
        outs = list(chunk_iter(inputs, feature_extractor, 30, 5, 5))
        self.assertEqual(len(outs), 5)
        self.assertEqual([o["stride"] for o in outs], [(30, 0, 5), (30, 5, 5), (30, 5, 5), (30, 5, 5), (20, 5, 0)])
        self.assertEqual([o["input_values"].shape for o in outs], [(1, 30), (1, 30), (1, 30), (1, 30), (1, 20)])
        self.assertEqual([o["is_last"] for o in outs], [False, False, False, False, True])
        # (0, 25)
        self.assertEqual(nested_simplify(input_values[:, :30]), nested_simplify(outs[0]["input_values"]))
        # (25, 45)
        self.assertEqual(nested_simplify(input_values[:, 20:50]), nested_simplify(outs[1]["input_values"]))
        # (45, 65)
        self.assertEqual(nested_simplify(input_values[:, 40:70]), nested_simplify(outs[2]["input_values"]))
        # (65, 85)
        self.assertEqual(nested_simplify(input_values[:, 60:90]), nested_simplify(outs[3]["input_values"]))
        # (85, 100)
        self.assertEqual(nested_simplify(input_values[:, 80:100]), nested_simplify(outs[4]["input_values"]))