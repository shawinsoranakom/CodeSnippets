def test_special_terminals(self):
        """Test with special terminal types."""
        special_terms = [
            "dumb",  # Minimal terminal
            "unknown",  # Should fall back to defaults
            "linux",  # Linux console
            "screen",  # GNU Screen
            "tmux",  # tmux
        ]

        # Get all string capabilities from ncurses
        for term in special_terms:
            with self.subTest(term=term):
                all_caps = self.infocmp(term)
                ncurses_code = dedent(
                    f"""
                    import _curses
                    import json
                    import sys

                    try:
                        _curses.setupterm({repr(term)}, 1)
                        results = {{}}
                        for cap in {repr(all_caps)}:
                            try:
                                val = _curses.tigetstr(cap)
                                if val is None:
                                    results[cap] = None
                                elif val == -1:
                                    results[cap] = -1
                                else:
                                    # Convert bytes to list of ints for JSON
                                    results[cap] = list(val)
                            except BaseException:
                                results[cap] = "error"
                        print(json.dumps(results))
                    except Exception as e:
                        print(json.dumps({{"error": str(e)}}))
                    """
                )

                # Get ncurses results
                result = subprocess.run(
                    [sys.executable, "-c", ncurses_code],
                    capture_output=True,
                    text=True,
                )
                if result.returncode != 0:
                    self.fail(
                        f"Failed to get ncurses data for {term}: {result.stderr}"
                    )

                try:
                    ncurses_data = json.loads(result.stdout)
                except json.JSONDecodeError:
                    self.fail(
                        f"Failed to parse ncurses output for {term}: {result.stdout}"
                    )

                if "error" in ncurses_data and len(ncurses_data) == 1:
                    # ncurses failed to setup this terminal
                    # PyREPL should still work with fallback
                    ti = terminfo.TermInfo(term, fallback=True)
                    continue

                ti = terminfo.TermInfo(term, fallback=False)

                # Compare all capabilities
                for cap in all_caps:
                    if cap not in ncurses_data:
                        continue

                    with self.subTest(term=term, capability=cap):
                        ncurses_val = ncurses_data[cap]
                        if isinstance(ncurses_val, list):
                            # Convert back to bytes
                            ncurses_val = bytes(ncurses_val)

                        pyrepl_val = ti.get(cap)

                        # Both should return the same value
                        self.assertEqual(
                            pyrepl_val,
                            ncurses_val,
                            f"Capability {cap} for {term}: "
                            f"ncurses={repr(ncurses_val)}, "
                            f"pyrepl={repr(pyrepl_val)}",
                        )