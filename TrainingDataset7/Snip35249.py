def test_parse_html_in_script(self):
        parse_html('<script>var a = "<p" + ">";</script>')
        parse_html("""
            <script>
            var js_sha_link='<p>***</p>';
            </script>
        """)

        # script content will be parsed to text
        dom = parse_html("""
            <script><p>foo</p> '</scr'+'ipt>' <span>bar</span></script>
        """)
        self.assertEqual(len(dom.children), 1)
        self.assertEqual(dom.children[0], "<p>foo</p> '</scr'+'ipt>' <span>bar</span>")