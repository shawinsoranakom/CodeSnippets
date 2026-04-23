def setUp(self):
        name = self.id().split('.')[-1]
        if name in _tests_needing_symlinks and not self.can_symlink:
            self.skipTest('requires symlinks')
        self.walk_path = self.cls(self.base, "TEST1")
        self.sub1_path = self.walk_path / "SUB1"
        self.sub11_path = self.sub1_path / "SUB11"
        self.sub2_path = self.walk_path / "SUB2"
        self.link_path = self.sub2_path / "link"
        self.sub2_tree = (self.sub2_path, [], ["tmp3"])

        # Build:
        #     TESTFN/
        #       TEST1/              a file kid and two directory kids
        #         tmp1
        #         SUB1/             a file kid and a directory kid
        #           tmp2
        #           SUB11/          no kids
        #         SUB2/             a file kid and a dirsymlink kid
        #           tmp3
        #           link/           a symlink to TEST2
        #           broken_link
        #           broken_link2
        #       TEST2/
        #         tmp4              a lone file
        t2_path = self.cls(self.base, "TEST2")
        os.makedirs(self.sub11_path)
        os.makedirs(self.sub2_path)
        os.makedirs(t2_path)

        tmp1_path = self.walk_path / "tmp1"
        tmp2_path = self.sub1_path / "tmp2"
        tmp3_path = self.sub2_path / "tmp3"
        tmp4_path = self.cls(self.base, "TEST2", "tmp4")
        for path in tmp1_path, tmp2_path, tmp3_path, tmp4_path:
            with open(path, "w", encoding='utf-8') as f:
                f.write(f"I'm {path} and proud of it.  Blame test_pathlib.\n")

        if self.can_symlink:
            broken_link_path = self.sub2_path / "broken_link"
            broken_link2_path = self.sub2_path / "broken_link2"
            os.symlink(t2_path, self.link_path, target_is_directory=True)
            os.symlink('broken', broken_link_path)
            os.symlink(os.path.join('tmp3', 'broken'), broken_link2_path)
            self.sub2_tree = (self.sub2_path, [], ["broken_link", "broken_link2", "link", "tmp3"])
        sub21_path= self.sub2_path / "SUB21"
        tmp5_path = sub21_path / "tmp3"
        broken_link3_path = self.sub2_path / "broken_link3"

        os.makedirs(sub21_path)
        tmp5_path.write_text("I am tmp5, blame test_pathlib.")
        if self.can_symlink:
            os.symlink(tmp5_path, broken_link3_path)
            self.sub2_tree[2].append('broken_link3')
            self.sub2_tree[2].sort()
        os.chmod(sub21_path, 0)
        try:
            os.listdir(sub21_path)
        except PermissionError:
            self.sub2_tree[1].append('SUB21')
        else:
            os.chmod(sub21_path, stat.S_IRWXU)
            os.unlink(tmp5_path)
            os.rmdir(sub21_path)