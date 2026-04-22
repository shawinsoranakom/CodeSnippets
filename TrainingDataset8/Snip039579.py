def test_tensorflow_session(self):
        tf_config = tf.compat.v1.ConfigProto()
        tf_session = tf.compat.v1.Session(config=tf_config)
        self.assertEqual(get_hash(tf_session), get_hash(tf_session))

        tf_session2 = tf.compat.v1.Session(config=tf_config)
        self.assertNotEqual(get_hash(tf_session), get_hash(tf_session2))