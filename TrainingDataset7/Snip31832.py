def test_404(self):
        with self.assertRaises(HTTPError) as err:
            self.urlopen("/")
        err.exception.close()
        self.assertEqual(err.exception.code, 404, "Expected 404 response")