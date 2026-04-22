def test_socket(self):
        a = socket.socket()
        b = socket.socket()

        self.assertEqual(get_hash(a), get_hash(a))
        self.assertNotEqual(get_hash(a), get_hash(b))