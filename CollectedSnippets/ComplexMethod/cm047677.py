def write_rows(self, rows):
        # we now group the translations by source. That means one translation per source.
        grouped_rows = {}
        modules = set()
        for module, type, name, res_id, src, trad, comments in rows:
            row = grouped_rows.setdefault(src, {})
            row.setdefault('modules', set()).add(module)
            if not row.get('translation') and trad != src:
                row['translation'] = trad
            row.setdefault('tnrs', []).append((type, name, res_id))
            row.setdefault('comments', set()).update(comments)
            modules.add(module)

        for src, row in sorted(grouped_rows.items()):
            if not self.lang:
                # translation template, so no translation value
                row['translation'] = ''
            elif not row.get('translation'):
                row['translation'] = ''
            self.add_entry(sorted(row['modules']), sorted(row['tnrs']), src, row['translation'], sorted(row['comments']))

        import odoo.release as release
        self.po.header = "Translation of %s.\n" \
                    "This file contains the translation of the following modules:\n" \
                    "%s" % (release.description, ''.join("\t* %s\n" % m for m in modules))
        now = datetime.utcnow().strftime('%Y-%m-%d %H:%M+0000')
        self.po.metadata = {
            'Project-Id-Version': "%s %s" % (release.description, release.version),
            'Report-Msgid-Bugs-To': '',
            'POT-Creation-Date': now,
            'PO-Revision-Date': now,
            'Last-Translator': '',
            'Language-Team': '',
            'MIME-Version': '1.0',
            'Content-Type': 'text/plain; charset=UTF-8',
            'Content-Transfer-Encoding': '',
            'Plural-Forms': '',
        }

        # buffer expects bytes
        self.buffer.write(str(self.po).encode())