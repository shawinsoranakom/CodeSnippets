def _run_makemessages(self, **options):
        out = StringIO()
        management.call_command(
            "makemessages", locale=[LOCALE], verbosity=2, stdout=out, **options
        )
        output = out.getvalue()
        self.assertTrue(os.path.exists(self.PO_FILE))
        with open(self.PO_FILE) as fp:
            po_contents = fp.read()
        return output, po_contents