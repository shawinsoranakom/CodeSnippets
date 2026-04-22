def test_tf_saved_model(self):
        tempdir = tempfile.TemporaryDirectory()

        model = tf.keras.models.Sequential(
            [
                tf.keras.layers.Dense(512, activation="relu", input_shape=(784,)),
            ]
        )
        model.save(tempdir.name)

        a = tf.saved_model.load(tempdir.name)
        b = tf.saved_model.load(tempdir.name)

        self.assertEqual(get_hash(a), get_hash(a))
        self.assertNotEqual(get_hash(a), get_hash(b))