def test_choices_generates_select_widget(self):
        """A TextField with choices uses a Select widget."""
        f = models.TextField(choices=[("A", "A"), ("B", "B")])
        self.assertIsInstance(f.formfield().widget, forms.Select)