def test_invalid_block_suggestion(self):
        """
        Error messages should include the unexpected block name and be in all
        English.
        """
        engine = self._engine()
        msg = (
            "Invalid block tag on line 1: 'endblock', expected 'elif', 'else' "
            "or 'endif'. Did you forget to register or load this tag?"
        )
        with self.settings(USE_I18N=True), translation.override("de"):
            with self.assertRaisesMessage(TemplateSyntaxError, msg):
                engine.from_string("{% if 1 %}lala{% endblock %}{% endif %}")