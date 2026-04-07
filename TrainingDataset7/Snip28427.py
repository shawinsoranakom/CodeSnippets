def test_render_empty_file_field(self):
        class DocumentForm(forms.ModelForm):
            class Meta:
                model = Document
                fields = "__all__"

        doc = Document.objects.create()
        form = DocumentForm(instance=doc)
        self.assertHTMLEqual(
            str(form["myfile"]), '<input id="id_myfile" name="myfile" type="file">'
        )