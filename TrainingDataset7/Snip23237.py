def test_html_does_not_mask_exceptions(self):
        """
        A ClearableFileInput should not mask exceptions produced while
        checking that it has a value.
        """

        class FailingURLFieldFile:
            @property
            def url(self):
                raise ValueError("Canary")

            def __str__(self):
                return "value"

        with self.assertRaisesMessage(ValueError, "Canary"):
            self.widget.render("myfile", FailingURLFieldFile())