def test_iframe(self):
        """Test components.iframe"""
        components.iframe("http://not.a.url", width=200, scrolling=True)

        el = self.get_delta_from_queue().new_element
        self.assertEqual(el.iframe.src, "http://not.a.url")
        self.assertEqual(el.iframe.srcdoc, "")
        self.assertEqual(el.iframe.width, 200)
        self.assertTrue(el.iframe.has_width)
        self.assertTrue(el.iframe.scrolling)