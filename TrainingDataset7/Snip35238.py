def test_msg_prefix(self):
        msg_prefix = "Prefix"
        msg = f"{msg_prefix}: No templates used to render the response"
        with self.assertRaisesMessage(AssertionError, msg):
            with self.assertTemplateUsed(
                "template_used/base.html", msg_prefix=msg_prefix
            ):
                pass

        with self.assertRaisesMessage(AssertionError, msg):
            with self.assertTemplateUsed(
                template_name="template_used/base.html",
                msg_prefix=msg_prefix,
            ):
                pass

        msg = (
            f"{msg_prefix}: Template 'template_used/base.html' was not a "
            f"template used to render the response. Actual template(s) used: "
            f"template_used/alternative.html"
        )
        with self.assertRaisesMessage(AssertionError, msg):
            with self.assertTemplateUsed(
                "template_used/base.html", msg_prefix=msg_prefix
            ):
                render_to_string("template_used/alternative.html")