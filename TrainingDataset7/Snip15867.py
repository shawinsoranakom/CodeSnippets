def test_custom_project_template_from_tarball_by_url_django_user_agent(self):
        user_agent = None

        def serve_template(request, *args, **kwargs):
            nonlocal user_agent
            user_agent = request.headers["User-Agent"]
            return serve(request, *args, **kwargs)

        old_urlpatterns = urls.urlpatterns[:]
        try:
            urls.urlpatterns += [
                path(
                    "user_agent_check/<path:path>",
                    serve_template,
                    {"document_root": os.path.join(urls.here, "custom_templates")},
                ),
            ]

            template_url = (
                f"{self.live_server_url}/user_agent_check/project_template.tgz"
            )
            args = ["startproject", "--template", template_url, "urltestproject"]
            _, err = self.run_django_admin(args)

            self.assertNoOutput(err)
            self.assertIn("Django/%s" % get_version(), user_agent)
        finally:
            urls.urlpatterns = old_urlpatterns