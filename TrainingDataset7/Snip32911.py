def test_script(self):
        self.assertEqual(
            escapejs_filter(r"<script>and this</script>"),
            "\\u003Cscript\\u003Eand this\\u003C/script\\u003E",
        )