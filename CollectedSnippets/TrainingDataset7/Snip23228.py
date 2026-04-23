def test_html_escaped(self):
        """
        A ClearableFileInput should escape name, filename, and URL
        when rendering HTML (#15182).
        """

        class StrangeFieldFile:
            url = "something?chapter=1&sect=2&copy=3&lang=en"

            def __str__(self):
                return """something<div onclick="alert('oops')">.jpg"""

        self.check_html(
            ClearableFileInput(),
            "my<div>file",
            StrangeFieldFile(),
            html=("""
                Currently:
                <a href="something?chapter=1&amp;sect=2&amp;copy=3&amp;lang=en">
                something&lt;div onclick=&quot;alert(&#x27;oops&#x27;)&quot;&gt;.jpg</a>
                <input type="checkbox" name="my&lt;div&gt;file-clear"
                    id="my&lt;div&gt;file-clear_id">
                <label for="my&lt;div&gt;file-clear_id">Clear</label><br>
                Change: <input type="file" name="my&lt;div&gt;file">
                """),
        )