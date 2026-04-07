def write_po_file(self, potfile, locale):
        """
        Create or update the PO file for self.domain and `locale`.
        Use contents of the existing `potfile`.

        Use msgmerge and msgattrib GNU gettext utilities.
        """
        basedir = os.path.join(os.path.dirname(potfile), locale, "LC_MESSAGES")
        os.makedirs(basedir, exist_ok=True)
        pofile = os.path.join(basedir, "%s.po" % self.domain)

        if os.path.exists(pofile):
            args = ["msgmerge", *self.msgmerge_options, pofile, potfile]
            _, errors, status = popen_wrapper(args)
            if errors:
                if status != STATUS_OK:
                    raise CommandError(
                        "errors happened while running msgmerge\n%s" % errors
                    )
                elif self.verbosity > 0:
                    self.stdout.write(errors)
            msgs = Path(pofile).read_text(encoding="utf-8")
        else:
            with open(potfile, encoding="utf-8") as fp:
                msgs = fp.read()
            if not self.invoked_for_django:
                msgs = self.copy_plural_forms(msgs, locale)
        msgs = normalize_eols(msgs)
        msgs = msgs.replace(
            "#. #-#-#-#-#  %s.pot (PACKAGE VERSION)  #-#-#-#-#\n" % self.domain, ""
        )
        with open(pofile, "w", encoding="utf-8") as fp:
            fp.write(msgs)

        if self.no_obsolete:
            args = ["msgattrib", *self.msgattrib_options, "-o", pofile, pofile]
            msgs, errors, status = popen_wrapper(args)
            if errors:
                if status != STATUS_OK:
                    raise CommandError(
                        "errors happened while running msgattrib\n%s" % errors
                    )
                elif self.verbosity > 0:
                    self.stdout.write(errors)