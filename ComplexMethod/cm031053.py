def test_walk_bottom_up(self):
        seen_root = seen_dira = seen_dirb = seen_dirc = seen_dird = False
        for path, dirnames, filenames in self.root.walk(top_down=False):
            if path == self.root:
                self.assertFalse(seen_root)
                self.assertTrue(seen_dira)
                self.assertTrue(seen_dirb)
                self.assertTrue(seen_dirc)
                self.assertEqual(sorted(dirnames), ['dirA', 'dirB', 'dirC'])
                self.assertEqual(sorted(filenames),
                                 ['brokenLink', 'brokenLinkLoop', 'fileA', 'linkA', 'linkB']
                                 if self.ground.can_symlink else ['fileA'])
                seen_root = True
            elif path == self.root / 'dirA':
                self.assertFalse(seen_root)
                self.assertFalse(seen_dira)
                self.assertEqual(dirnames, [])
                self.assertEqual(filenames, ['linkC'] if self.ground.can_symlink else [])
                seen_dira = True
            elif path == self.root / 'dirB':
                self.assertFalse(seen_root)
                self.assertFalse(seen_dirb)
                self.assertEqual(dirnames, [])
                self.assertEqual(filenames, ['fileB'])
                seen_dirb = True
            elif path == self.root / 'dirC':
                self.assertFalse(seen_root)
                self.assertFalse(seen_dirc)
                self.assertTrue(seen_dird)
                self.assertEqual(dirnames, ['dirD'])
                self.assertEqual(sorted(filenames), ['fileC', 'novel.txt'])
                seen_dirc = True
            elif path == self.root / 'dirC' / 'dirD':
                self.assertFalse(seen_root)
                self.assertFalse(seen_dirc)
                self.assertFalse(seen_dird)
                self.assertEqual(dirnames, [])
                self.assertEqual(filenames, ['fileD'])
                seen_dird = True
            else:
                raise AssertionError(f"Unexpected path: {path}")
        self.assertTrue(seen_root)