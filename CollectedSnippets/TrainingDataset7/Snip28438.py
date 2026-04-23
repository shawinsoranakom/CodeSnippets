def test_media_on_modelform(self):
        # Similar to a regular Form class you can define custom media to be
        # used on the ModelForm.
        f = ModelFormWithMedia()
        self.assertHTMLEqual(
            str(f.media),
            '<link href="/some/form/css" media="all" rel="stylesheet">'
            '<script src="/some/form/javascript"></script>',
        )