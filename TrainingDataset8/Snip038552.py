def test_html(self):
        """Test components.html"""
        html = r"<html><body>An HTML string!</body></html>"
        components.html(html, width=200, scrolling=True)

        el = self.get_delta_from_queue().new_element
        self.assertEqual(el.iframe.src, "")
        self.assertEqual(el.iframe.srcdoc, html)
        self.assertEqual(el.iframe.width, 200)
        self.assertTrue(el.iframe.has_width)
        self.assertTrue(el.iframe.scrolling)