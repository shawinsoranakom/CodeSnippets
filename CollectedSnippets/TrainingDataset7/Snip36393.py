def test_json_script(self):
        tests = (
            # "<", ">" and "&" are quoted inside JSON strings
            (
                (
                    "&<>",
                    '<script id="test_id" type="application/json">'
                    '"\\u0026\\u003C\\u003E"</script>',
                )
            ),
            # "<", ">" and "&" are quoted inside JSON objects
            (
                {"a": "<script>test&ing</script>"},
                '<script id="test_id" type="application/json">'
                '{"a": "\\u003Cscript\\u003Etest\\u0026ing\\u003C/script\\u003E"}'
                "</script>",
            ),
            # Lazy strings are quoted
            (
                lazystr("&<>"),
                '<script id="test_id" type="application/json">"\\u0026\\u003C\\u003E"'
                "</script>",
            ),
            (
                {"a": lazystr("<script>test&ing</script>")},
                '<script id="test_id" type="application/json">'
                '{"a": "\\u003Cscript\\u003Etest\\u0026ing\\u003C/script\\u003E"}'
                "</script>",
            ),
        )
        for arg, expected in tests:
            with self.subTest(arg=arg):
                self.assertEqual(json_script(arg, "test_id"), expected)