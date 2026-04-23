def test_mac_ver(self):
        res = platform.mac_ver()

        if platform.uname().system == 'Darwin':
            # We are on a macOS system, check that the right version
            # information is returned
            output = subprocess.check_output(['sw_vers'], text=True)
            for line in output.splitlines():
                if line.startswith('ProductVersion:'):
                    real_ver = line.strip().split()[-1]
                    break
            else:
                self.fail(f"failed to parse sw_vers output: {output!r}")

            result_list = res[0].split('.')
            expect_list = real_ver.split('.')
            len_diff = len(result_list) - len(expect_list)
            # On Snow Leopard, sw_vers reports 10.6.0 as 10.6
            if len_diff > 0:
                expect_list.extend(['0'] * len_diff)
            # For compatibility with older binaries, macOS 11.x may report
            # itself as '10.16' rather than '11.x.y'.
            if result_list != ['10', '16']:
                self.assertEqual(result_list, expect_list)

            # res[1] claims to contain
            # (version, dev_stage, non_release_version)
            # That information is no longer available
            self.assertEqual(res[1], ('', '', ''))

            if sys.byteorder == 'little':
                self.assertIn(res[2], ('i386', 'x86_64', 'arm64'))
            else:
                self.assertEqual(res[2], 'PowerPC')