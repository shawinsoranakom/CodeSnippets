def test_tz_template_context_processor(self):
        """
        Test the django.template.context_processors.tz template context
        processor.
        """
        tpl = Template("{{ TIME_ZONE }}")
        context = Context()
        self.assertEqual(tpl.render(context), "")
        request_context = RequestContext(
            HttpRequest(), processors=[context_processors.tz]
        )
        self.assertEqual(tpl.render(request_context), "Africa/Nairobi")