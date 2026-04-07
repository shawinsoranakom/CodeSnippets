def test_set_alters_data(self):
        template = self.engine.from_string(
            "{% set test = User.objects.create_superuser("
            "username='evil', email='a@b.com', password='xxx') %}"
            "{{ test }}"
        )
        with self.assertRaises(jinja2.exceptions.SecurityError):
            template.render(context={"User": User})
        self.assertEqual(User.objects.count(), 0)