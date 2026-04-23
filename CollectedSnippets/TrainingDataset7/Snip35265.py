def test_contains_html(self):
        response = HttpResponse("""<body>
        This is a form: <form method="get">
            <input type="text" name="Hello" />
        </form></body>""")

        self.assertNotContains(response, "<input name='Hello' type='text'>")
        self.assertContains(response, '<form method="get">')

        self.assertContains(response, "<input name='Hello' type='text'>", html=True)
        self.assertNotContains(response, '<form method="get">', html=True)

        invalid_response = HttpResponse("""<body <bad>>""")

        with self.assertRaises(AssertionError):
            self.assertContains(invalid_response, "<p></p>")

        with self.assertRaises(AssertionError):
            self.assertContains(response, '<p "whats" that>')