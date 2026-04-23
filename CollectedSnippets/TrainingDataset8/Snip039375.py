def test_PIL_image(self):
        im1 = Image.new("RGB", (50, 50), (220, 20, 60))
        im2 = Image.new("RGB", (50, 50), (30, 144, 255))
        im3 = Image.new("RGB", (50, 50), (220, 20, 60))

        self.assertEqual(get_hash(im1), get_hash(im3))
        self.assertNotEqual(get_hash(im1), get_hash(im2))

        # Check for big PIL images, they converted to numpy array with size
        # bigger than _NP_SIZE_LARGE
        # 1000 * 1000 * 3 = 3_000_000 > _NP_SIZE_LARGE = 1_000_000
        im4 = Image.new("RGB", (1000, 1000), (100, 20, 60))
        im5 = Image.new("RGB", (1000, 1000), (100, 20, 60))
        im6 = Image.new("RGB", (1000, 1000), (101, 21, 61))

        im4_np_array = np.frombuffer(im4.tobytes(), dtype="uint8")
        self.assertGreater(im4_np_array.size, _NP_SIZE_LARGE)

        self.assertEqual(get_hash(im4), get_hash(im5))
        self.assertNotEqual(get_hash(im5), get_hash(im6))