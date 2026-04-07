def test_invalid_urls(self):
        response = self.client.get("~%A9helloworld")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.context["request_path"], "/~%25A9helloworld")

        response = self.client.get("d%aao%aaw%aan%aal%aao%aaa%aad%aa/")
        self.assertEqual(
            response.context["request_path"],
            "/d%25AAo%25AAw%25AAn%25AAl%25AAo%25AAa%25AAd%25AA",
        )

        response = self.client.get("/%E2%99%E2%99%A5/")
        self.assertEqual(response.context["request_path"], "/%25E2%2599%E2%99%A5/")

        response = self.client.get("/%E2%98%8E%E2%A9%E2%99%A5/")
        self.assertEqual(
            response.context["request_path"], "/%E2%98%8E%25E2%25A9%E2%99%A5/"
        )