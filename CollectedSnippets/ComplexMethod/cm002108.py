def test_chunk_iterator(self):
        feature_extractor = AutoFeatureExtractor.from_pretrained("facebook/wav2vec2-base-960h")
        inputs = torch.arange(100).long()
        outs = list(chunk_iter(inputs, feature_extractor, 100, 0, 0))

        self.assertEqual(len(outs), 1)
        self.assertEqual([o["stride"] for o in outs], [(100, 0, 0)])
        self.assertEqual([o["input_values"].shape for o in outs], [(1, 100)])
        self.assertEqual([o["is_last"] for o in outs], [True])

        # two chunks no stride
        outs = list(chunk_iter(inputs, feature_extractor, 50, 0, 0))
        self.assertEqual(len(outs), 2)
        self.assertEqual([o["stride"] for o in outs], [(50, 0, 0), (50, 0, 0)])
        self.assertEqual([o["input_values"].shape for o in outs], [(1, 50), (1, 50)])
        self.assertEqual([o["is_last"] for o in outs], [False, True])

        # two chunks incomplete last
        outs = list(chunk_iter(inputs, feature_extractor, 80, 0, 0))
        self.assertEqual(len(outs), 2)
        self.assertEqual([o["stride"] for o in outs], [(80, 0, 0), (20, 0, 0)])
        self.assertEqual([o["input_values"].shape for o in outs], [(1, 80), (1, 20)])
        self.assertEqual([o["is_last"] for o in outs], [False, True])

        # one chunk since first is also last, because it contains only data
        # in the right strided part we just mark that part as non stride
        # This test is specifically crafted to trigger a bug if next chunk
        # would be ignored by the fact that all the data would be
        # contained in the strided left data.
        outs = list(chunk_iter(inputs, feature_extractor, 105, 5, 5))
        self.assertEqual(len(outs), 1)
        self.assertEqual([o["stride"] for o in outs], [(100, 0, 0)])
        self.assertEqual([o["input_values"].shape for o in outs], [(1, 100)])
        self.assertEqual([o["is_last"] for o in outs], [True])