def remove_potfiles(self):
        for path in self.locale_paths:
            pot_path = os.path.join(path, "%s.pot" % self.domain)
            if os.path.exists(pot_path):
                os.unlink(pot_path)