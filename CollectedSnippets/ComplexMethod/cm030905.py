def _test_extra_groups_impl(self, *, gid, group_list):
        name_group = _get_test_grp_name()

        if grp is not None:
            group_list.append(name_group)

        try:
            output = subprocess.check_output(
                    [sys.executable, "-c",
                     "import os, sys, json; json.dump(os.getgroups(), sys.stdout)"],
                    extra_groups=group_list)
        except PermissionError as e:
            self.assertIsNone(e.filename)
            self.skipTest("setgroup() EPERM; this test may require root.")
        else:
            parent_groups = os.getgroups()
            child_groups = json.loads(output)

            if grp is not None:
                desired_gids = [grp.getgrnam(g).gr_gid if isinstance(g, str) else g
                                for g in group_list]
            else:
                desired_gids = group_list

            self.assertEqual(set(desired_gids), set(child_groups))

        if grp is None:
            with self.assertRaises(ValueError):
                subprocess.check_call(ZERO_RETURN_CMD,
                                      extra_groups=[name_group])