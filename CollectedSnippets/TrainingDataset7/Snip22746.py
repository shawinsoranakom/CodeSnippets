def test_error_messages_escaping(self):
        # The forms layer doesn't escape input values directly because error
        # messages might be presented in non-HTML contexts. Instead, the
        # message is marked for escaping by the template engine, so a template
        # is needed to trigger the escaping.
        t = Template("{{ form.errors }}")

        class SomeForm(Form):
            field = ChoiceField(choices=[("one", "One")])

        f = SomeForm({"field": "<script>"})
        self.assertHTMLEqual(
            t.render(Context({"form": f})),
            '<ul class="errorlist"><li>field<ul class="errorlist" id="id_field_error">'
            "<li>Select a valid choice. &lt;script&gt; is not one of the "
            "available choices.</li></ul></li></ul>",
        )

        class SomeForm(Form):
            field = MultipleChoiceField(choices=[("one", "One")])

        f = SomeForm({"field": ["<script>"]})
        self.assertHTMLEqual(
            t.render(Context({"form": f})),
            '<ul class="errorlist"><li>field<ul class="errorlist" id="id_field_error">'
            "<li>Select a valid choice. &lt;script&gt; is not one of the "
            "available choices.</li></ul></li></ul>",
        )

        class SomeForm(Form):
            field = ModelMultipleChoiceField(ChoiceModel.objects.all())

        f = SomeForm({"field": ["<script>"]})
        self.assertHTMLEqual(
            t.render(Context({"form": f})),
            '<ul class="errorlist"><li>field<ul class="errorlist" id="id_field_error">'
            "<li>“&lt;script&gt;” is not a valid value.</li>"
            "</ul></li></ul>",
        )