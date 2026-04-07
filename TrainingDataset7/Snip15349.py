def test_template_detail_path_traversal(self):
        cases = ["/etc/passwd", "../passwd"]
        for fpath in cases:
            with self.subTest(path=fpath):
                response = self.client.get(
                    reverse("django-admindocs-templates", args=[fpath]),
                )
                self.assertEqual(response.status_code, 400)