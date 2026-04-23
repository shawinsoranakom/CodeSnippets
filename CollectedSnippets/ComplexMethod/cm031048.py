def test_tparm_multiple_params(self):
        """Test tparm with capabilities using multiple parameters."""
        term = "xterm"
        ti = terminfo.TermInfo(term, fallback=False)

        # Test capabilities that take parameters
        param_caps = {
            "cub": 1,  # cursor_left with count
            "cuf": 1,  # cursor_right with count
            "cuu": 1,  # cursor_up with count
            "cud": 1,  # cursor_down with count
            "dch": 1,  # delete_character with count
            "ich": 1,  # insert_character with count
        }

        # Get all capabilities from PyREPL first
        pyrepl_caps = {}
        for cap in param_caps:
            cap_value = ti.get(cap)
            if cap_value and cap_value not in {
                ABSENT_STRING,
                CANCELLED_STRING,
            }:
                pyrepl_caps[cap] = cap_value

        if not pyrepl_caps:
            self.skipTest("No parametrized capabilities found")

        # Get ncurses results in subprocess
        ncurses_code = dedent(
            f"""
            import _curses
            import json
            _curses.setupterm({repr(term)}, 1)

            param_caps = {repr(param_caps)}
            test_values = [1, 5, 10, 99]
            results = {{}}

            for cap in param_caps:
                cap_value = _curses.tigetstr(cap)
                if cap_value and cap_value != -1:
                    for value in test_values:
                        try:
                            result = _curses.tparm(cap_value, value)
                            results[f"{{cap}},{{value}}"] = list(result)
                        except Exception as e:
                            results[f"{{cap}},{{value}}"] = {{"error": str(e)}}

            print(json.dumps(results))
            """
        )

        result = subprocess.run(
            [sys.executable, "-c", ncurses_code],
            capture_output=True,
            text=True,
        )
        self.assertEqual(
            result.returncode, 0, f"Failed to run ncurses: {result.stderr}"
        )
        ncurses_data = json.loads(result.stdout)

        for cap, cap_value in pyrepl_caps.items():
            with self.subTest(capability=cap):
                # Test with different parameter values
                for value in [1, 5, 10, 99]:
                    key = f"{cap},{value}"
                    if key in ncurses_data:
                        if (
                            isinstance(ncurses_data[key], dict)
                            and "error" in ncurses_data[key]
                        ):
                            self.fail(
                                f"ncurses tparm failed: {ncurses_data[key]['error']}"
                            )
                        std_result = bytes(ncurses_data[key])

                        pyrepl_result = terminfo.tparm(cap_value, value)
                        self.assertEqual(
                            pyrepl_result,
                            std_result,
                            f"tparm({cap}, {value}): "
                            f"std={repr(std_result)}, pyrepl={repr(pyrepl_result)}",
                        )