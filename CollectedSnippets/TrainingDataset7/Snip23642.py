def _assert_about(self, response):
        response.render()
        self.assertContains(response, "<h1>About</h1>")