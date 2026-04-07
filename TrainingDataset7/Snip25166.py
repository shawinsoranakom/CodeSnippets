def _create_translation_from_string(content):
            with tempfile.TemporaryDirectory() as dirname:
                po_path = Path(dirname).joinpath("fr", "LC_MESSAGES", "django.po")
                po_path.parent.mkdir(parents=True)
                po_path.write_text(content)
                errors = popen_wrapper(
                    ["msgfmt", "-o", po_path.with_suffix(".mo"), po_path]
                )[1]
                if errors:
                    self.fail(f"msgfmt compilation error: {errors}")
                return gettext_module.translation(
                    domain="django",
                    localedir=dirname,
                    languages=["fr"],
                )