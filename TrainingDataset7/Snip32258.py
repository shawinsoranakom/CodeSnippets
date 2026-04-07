def test_x_robots_sitemap(self):
        response = self.client.get("/simple/index.xml")
        self.assertEqual(response.headers["X-Robots-Tag"], "noindex, noodp, noarchive")

        response = self.client.get("/simple/sitemap.xml")
        self.assertEqual(response.headers["X-Robots-Tag"], "noindex, noodp, noarchive")