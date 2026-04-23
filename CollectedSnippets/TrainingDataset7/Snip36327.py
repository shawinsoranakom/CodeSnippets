def test_stylesheet_keeps_lazy_urls(self):
        m = mock.Mock(return_value="test.css")
        stylesheet = feedgenerator.Stylesheet(SimpleLazyObject(m))
        m.assert_not_called()
        self.assertEqual(
            str(stylesheet), 'href="test.css" media="screen" type="text/css"'
        )
        m.assert_called_once()