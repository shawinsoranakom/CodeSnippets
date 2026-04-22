def test_tf_keras_model(self):
        a = tf.keras.applications.vgg16.VGG16(include_top=False, weights=None)
        b = tf.keras.applications.vgg16.VGG16(include_top=False, weights=None)

        self.assertEqual(get_hash(a), get_hash(a))
        self.assertNotEqual(get_hash(a), get_hash(b))