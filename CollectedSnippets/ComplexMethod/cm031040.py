def test_folds_and_gaps(self):
        test_cases = []
        for key in self.zones():
            tests = {"folds": [], "gaps": []}
            for zt in self.load_transition_examples(key):
                if zt.fold:
                    test_group = tests["folds"]
                elif zt.gap:
                    test_group = tests["gaps"]
                else:
                    # Assign a random variable here to disable the peephole
                    # optimizer so that coverage can see this line.
                    # See bpo-2506 for more information.
                    no_peephole_opt = None
                    continue

                # Cases are of the form key, dt, fold, offset
                dt = zt.anomaly_start - timedelta(seconds=1)
                test_group.append((dt, 0, zt.offset_before))
                test_group.append((dt, 1, zt.offset_before))

                dt = zt.anomaly_start
                test_group.append((dt, 0, zt.offset_before))
                test_group.append((dt, 1, zt.offset_after))

                dt = zt.anomaly_start + timedelta(seconds=1)
                test_group.append((dt, 0, zt.offset_before))
                test_group.append((dt, 1, zt.offset_after))

                dt = zt.anomaly_end - timedelta(seconds=1)
                test_group.append((dt, 0, zt.offset_before))
                test_group.append((dt, 1, zt.offset_after))

                dt = zt.anomaly_end
                test_group.append((dt, 0, zt.offset_after))
                test_group.append((dt, 1, zt.offset_after))

                dt = zt.anomaly_end + timedelta(seconds=1)
                test_group.append((dt, 0, zt.offset_after))
                test_group.append((dt, 1, zt.offset_after))

            for grp, test_group in tests.items():
                test_cases.append(((key, grp), test_group))

        for (key, grp), tests in test_cases:
            with self.subTest(key=key, grp=grp):
                tzi = self.zone_from_key(key)

                for dt, fold, offset in tests:
                    dt = dt.replace(fold=fold, tzinfo=tzi)

                    self.assertEqual(dt.tzname(), offset.tzname, dt)
                    self.assertEqual(dt.utcoffset(), offset.utcoffset, dt)
                    self.assertEqual(dt.dst(), offset.dst, dt)