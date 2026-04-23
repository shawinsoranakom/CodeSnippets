def test_keras_model(self):
        a = keras.applications.vgg16.VGG16(include_top=False, weights=None)
        b = keras.applications.vgg16.VGG16(include_top=False, weights=None)

        # This test still passes if we remove the default hash func for Keras
        # models. Ideally we'd seed the weights before creating the models
        # but not clear how to do so.
        self.assertEqual(get_hash(a), get_hash(a))
        self.assertNotEqual(get_hash(a), get_hash(b))