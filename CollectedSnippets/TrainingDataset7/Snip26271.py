def test_no_legacy_apis_imported(self):
        django_core_mail_path = Path(mail.__file__).parent
        django_path = django_core_mail_path.parent.parent.parent
        for abs_path in django_core_mail_path.glob("**/*.py"):
            allowed_exceptions = self.allowed_exceptions.copy()
            # RemovedInDjango70Warning.
            # The following will be removed after the deprecation period.
            if abs_path.name == "message.py":
                allowed_exceptions.update(
                    {
                        "email.charset",
                        "email.header.Header",
                        "email.mime.base.MIMEBase",
                        "email.mime.message.MIMEMessage",
                        "email.mime.multipart.MIMEMultipart",
                        "email.mime.text.MIMEText",
                        "email.utils.formataddr",
                        "email.utils.getaddresses",
                    }
                )
            path = abs_path.relative_to(django_path)
            with self.subTest(path=str(path)):
                collector = self.ImportCollector(abs_path.read_text())
                used_apis = collector.get_matching_imports(self.legacy_email_apis)
                used_apis -= allowed_exceptions
                self.assertEqual(
                    "\n".join(sorted(used_apis)),
                    "",
                    f"Python legacy email APIs used in {path}",
                )