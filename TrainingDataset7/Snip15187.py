def test_no_user(self):
        """{% get_admin_log %} works without specifying a user."""
        user = User(username="jondoe", password="secret", email="super@example.com")
        user.save()
        LogEntry.objects.log_actions(user.pk, [user], 1)
        context = Context({"log_entries": LogEntry.objects.all()})
        t = Template(
            "{% load log %}"
            "{% get_admin_log 100 as admin_log %}"
            "{% for entry in admin_log %}"
            "{{ entry|safe }}"
            "{% endfor %}"
        )
        self.assertEqual(t.render(context), "Added “jondoe”.")