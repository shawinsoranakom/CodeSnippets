def test_load_library_importerror(self):
        PlainHasher = type(
            "PlainHasher",
            (BasePasswordHasher,),
            {"algorithm": "plain", "library": "plain"},
        )
        msg = "Couldn't load 'PlainHasher' algorithm library: No module named 'plain'"
        with self.assertRaisesMessage(ValueError, msg):
            PlainHasher()._load_library()