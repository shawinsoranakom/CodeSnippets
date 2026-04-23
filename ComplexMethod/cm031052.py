def test_no_newline(self):
        env = os.environ.copy()
        env.pop("PYTHON_BASIC_REPL", "")
        env["PYTHON_BASIC_REPL"] = "1"

        commands = "print('Something pretty long', end='')\nexit()\n"
        expected_output_sequence = "Something pretty long>>> exit()"

        # gh-143394: The basic REPL needs the readline module to turn off
        # ECHO terminal attribute.
        if readline_module is not None:
            basic_output, basic_exit_code = self.run_repl(commands, env=env)
            self.assertEqual(basic_exit_code, 0)
            self.assertIn(expected_output_sequence, basic_output)

        output, exit_code = self.run_repl(commands)
        self.assertEqual(exit_code, 0)

        # Build patterns for escape sequences that don't affect cursor position
        # or visual output. Use terminfo to get platform-specific sequences,
        # falling back to hard-coded patterns for capabilities not in terminfo.
        from _pyrepl.terminfo import TermInfo
        ti = TermInfo(os.environ.get("TERM", ""))

        safe_patterns = []

        # smkx/rmkx - application cursor keys and keypad mode
        smkx = ti.get("smkx")
        rmkx = ti.get("rmkx")
        if smkx:
            safe_patterns.append(re.escape(smkx.decode("ascii")))
        if rmkx:
            safe_patterns.append(re.escape(rmkx.decode("ascii")))
        if not smkx and not rmkx:
            safe_patterns.append(r'\x1b\[\?1[hl]')  # application cursor keys
            safe_patterns.append(r'\x1b[=>]')  # application keypad mode

        # ich1 - insert character (only safe form that inserts exactly 1 char)
        ich1 = ti.get("ich1")
        if ich1:
            safe_patterns.append(re.escape(ich1.decode("ascii")) + r'(?=[ -~])')
        else:
            safe_patterns.append(r'\x1b\[(?:1)?@(?=[ -~])')

        # civis/cnorm - cursor visibility (may include cursor blinking control)
        civis = ti.get("civis")
        cnorm = ti.get("cnorm")
        if civis:
            safe_patterns.append(re.escape(civis.decode("ascii")))
        if cnorm:
            safe_patterns.append(re.escape(cnorm.decode("ascii")))
        if not civis and not cnorm:
            safe_patterns.append(r'\x1b\[\?25[hl]')  # cursor visibility
            safe_patterns.append(r'\x1b\[\?12[hl]')  # cursor blinking

        # rmam / smam - automatic margins
        rmam = ti.get("rmam")
        smam = ti.get("smam")
        if rmam:
            safe_patterns.append(re.escape(rmam.decode("ascii")))
        if smam:
            safe_patterns.append(re.escape(smam.decode("ascii")))
        if not rmam and not smam:
            safe_patterns.append(r'\x1b\[\?7l') # turn off automatic margins
            safe_patterns.append(r'\x1b\[\?7h') # turn on automatic margins

        # Modern extensions not in standard terminfo - always use patterns
        safe_patterns.append(r'\x1b\[\?2004[hl]')  # bracketed paste mode
        safe_patterns.append(r'\x1b\[\?12[hl]')  # cursor blinking (may be separate)
        safe_patterns.append(r'\x1b\[\?[01]c')  # device attributes

        safe_escapes = re.compile('|'.join(safe_patterns))
        cleaned_output = safe_escapes.sub('', output)
        self.assertIn(expected_output_sequence, cleaned_output)