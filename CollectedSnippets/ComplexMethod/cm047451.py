def test_conflict_markers(self):
        """ Test that there are no conflict markers left in Odoo files """
        import odoo.addons  # noqa: PLC0415

        counter = 0

        paths = sorted(os.path.abspath(p) for p in [*odoo.addons.__path__, *odoo.__path__])

        already_visited = set()
        for p in paths:
            if p in already_visited:
                continue
            for dp, _, file_names in os.walk(p):
                already_visited.add(dp)
                if 'node_modules' in dp:
                    continue
                for fn in file_names:
                    if fn.endswith(EXTENSIONS):
                        self.check_file(os.path.join(dp, fn))
                        counter += 1
        _logger.info('%s files tested', counter)