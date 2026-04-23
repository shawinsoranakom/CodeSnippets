def test_attributes(self):
        link = os_helper.can_hardlink()
        symlink = os_helper.can_symlink()

        dirname = os.path.join(self.path, "dir")
        os.mkdir(dirname)
        filename = self.create_file("file.txt")
        if link:
            try:
                os.link(filename, os.path.join(self.path, "link_file.txt"))
            except PermissionError as e:
                self.skipTest('os.link(): %s' % e)
        if symlink:
            os.symlink(dirname, os.path.join(self.path, "symlink_dir"),
                       target_is_directory=True)
            os.symlink(filename, os.path.join(self.path, "symlink_file.txt"))

        names = ['dir', 'file.txt']
        if link:
            names.append('link_file.txt')
        if symlink:
            names.extend(('symlink_dir', 'symlink_file.txt'))
        entries = self.get_entries(names)

        entry = entries['dir']
        self.check_entry(entry, 'dir', True, False, False)

        entry = entries['file.txt']
        self.check_entry(entry, 'file.txt', False, True, False)

        if link:
            entry = entries['link_file.txt']
            self.check_entry(entry, 'link_file.txt', False, True, False)

        if symlink:
            entry = entries['symlink_dir']
            self.check_entry(entry, 'symlink_dir', True, False, True)

            entry = entries['symlink_file.txt']
            self.check_entry(entry, 'symlink_file.txt', False, True, True)