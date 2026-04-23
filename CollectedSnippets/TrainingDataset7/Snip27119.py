def test_makemigrations_merge_dont_output_dependency_operations(self):
        """
        makemigrations --merge does not output any operations from apps that
        don't belong to a given app.
        """
        # Monkeypatch interactive questioner to auto accept
        with mock.patch("builtins.input", mock.Mock(return_value="N")):
            out = io.StringIO()
            with mock.patch(
                "django.core.management.color.supports_color", lambda *args: False
            ):
                call_command(
                    "makemigrations",
                    "conflicting_app_with_dependencies",
                    merge=True,
                    interactive=True,
                    stdout=out,
                )
            self.assertEqual(
                out.getvalue().lower(),
                "merging conflicting_app_with_dependencies\n"
                "  branch 0002_conflicting_second\n"
                "    + create model something\n"
                "  branch 0002_second\n"
                "    - delete model tribble\n"
                "    - remove field silly_field from author\n"
                "    + add field rating to author\n"
                "    + create model book\n"
                "\n"
                "merging will only work if the operations printed above do not "
                "conflict\n"
                "with each other (working on different fields or models)\n"
                "should these migration branches be merged? [y/n] ",
            )