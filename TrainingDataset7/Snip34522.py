def test_render_tag_error_in_extended_block(self):
        """Errors in extended block are displayed correctly."""
        e = self._engine(app_dirs=True)
        template = e.get_template("test_extends_block_error.html")
        context = Context()
        with self.assertRaises(TemplateDoesNotExist) as cm:
            template.render(context)
        if self.debug_engine:
            self.assertEqual(
                cm.exception.template_debug["before"],
                '{% block content %}{% include "index.html" %}',
            )
            self.assertEqual(
                cm.exception.template_debug["during"],
                '{% include "missing.html" %}',
            )
            self.assertEqual(
                cm.exception.template_debug["after"],
                '{% include "index.html" %}{% endblock %}\n',
            )
            self.assertEqual(
                cm.exception.template_debug["source_lines"][0],
                (1, '{% extends "test_extends_block_error_parent.html" %}\n'),
            )
            self.assertEqual(
                cm.exception.template_debug["source_lines"][1],
                (
                    2,
                    '{% block content %}{% include "index.html" %}'
                    '{% include "missing.html" %}'
                    '{% include "index.html" %}{% endblock %}\n',
                ),
            )
            self.assertEqual(cm.exception.template_debug["source_lines"][2], (3, ""))