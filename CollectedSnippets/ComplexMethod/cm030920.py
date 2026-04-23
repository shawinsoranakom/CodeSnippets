def test_nonascii(self):
        loc = locale.setlocale(locale.LC_CTYPE, None)
        if loc in ('C', 'POSIX'):
            # bpo-29240: On FreeBSD, if the LC_CTYPE locale is C or POSIX,
            # writing and reading non-ASCII bytes into/from a TTY works, but
            # readline or ncurses ignores non-ASCII bytes on read.
            self.skipTest(f"the LC_CTYPE locale is {loc!r}")
        if sys.flags.utf8_mode:
            encoding = locale.getencoding()
            encoding = codecs.lookup(encoding).name  # normalize the name
            if encoding != "utf-8":
                # gh-133711: The Python UTF-8 Mode ignores the LC_CTYPE locale
                # and always use the UTF-8 encoding.
                self.skipTest(f"the LC_CTYPE encoding is {encoding!r}")

        try:
            readline.add_history("\xEB\xEF")
        except UnicodeEncodeError as err:
            self.skipTest("Locale cannot encode test data: " + format(err))

        script = r"""import readline

is_editline = readline.backend == "editline"
inserted = "[\xEFnserted]"
macro = "|t\xEB[after]"
set_pre_input_hook = getattr(readline, "set_pre_input_hook", None)
if is_editline or not set_pre_input_hook:
    # The insert_line() call via pre_input_hook() does nothing with Editline,
    # so include the extra text that would have been inserted here
    macro = inserted + macro

if is_editline:
    readline.parse_and_bind(r'bind ^B ed-prev-char')
    readline.parse_and_bind(r'bind "\t" rl_complete')
    readline.parse_and_bind(r'bind -s ^A "{}"'.format(macro))
else:
    readline.parse_and_bind(r'Control-b: backward-char')
    readline.parse_and_bind(r'"\t": complete')
    readline.parse_and_bind(r'set disable-completion off')
    readline.parse_and_bind(r'set show-all-if-ambiguous off')
    readline.parse_and_bind(r'set show-all-if-unmodified off')
    readline.parse_and_bind(r'Control-a: "{}"'.format(macro))

def pre_input_hook():
    readline.insert_text(inserted)
    readline.redisplay()
if set_pre_input_hook:
    set_pre_input_hook(pre_input_hook)

def completer(text, state):
    if text == "t\xEB":
        if state == 0:
            print("text", ascii(text))
            print("line", ascii(readline.get_line_buffer()))
            print("indexes", readline.get_begidx(), readline.get_endidx())
            return "t\xEBnt"
        if state == 1:
            return "t\xEBxt"
    if text == "t\xEBx" and state == 0:
        return "t\xEBxt"
    return None
readline.set_completer(completer)

def display(substitution, matches, longest_match_length):
    print("substitution", ascii(substitution))
    print("matches", ascii(matches))
readline.set_completion_display_matches_hook(display)

print("result", ascii(input()))
print("history", ascii(readline.get_history_item(1)))
"""

        input = b"\x01"  # Ctrl-A, expands to "|t\xEB[after]"
        input += b"\x02" * len("[after]")  # Move cursor back
        input += b"\t\t"  # Display possible completions
        input += b"x\t"  # Complete "t\xEBx" -> "t\xEBxt"
        input += b"\r"
        output = run_pty(script, input)
        self.assertIn(b"text 't\\xeb'\r\n", output)
        self.assertIn(b"line '[\\xefnserted]|t\\xeb[after]'\r\n", output)
        if sys.platform == "darwin" or not is_editline:
            self.assertIn(b"indexes 11 13\r\n", output)
            # Non-macOS libedit does not handle non-ASCII bytes
            # the same way and generates character indices
            # rather than byte indices via get_begidx() and
            # get_endidx().  Ex: libedit2 3.1-20191231-2 on Debian
            # winds up with "indexes 10 12".  Stemming from the
            # start and end values calls back into readline.c's
            # rl_attempted_completion_function = flex_complete with:
            # (11, 13) instead of libreadline's (12, 15).

        if not is_editline and hasattr(readline, "set_pre_input_hook"):
            self.assertIn(b"substitution 't\\xeb'\r\n", output)
            self.assertIn(b"matches ['t\\xebnt', 't\\xebxt']\r\n", output)
        expected = br"'[\xefnserted]|t\xebxt[after]'"
        self.assertIn(b"result " + expected + b"\r\n", output)
        # bpo-45195: Sometimes, the newline character is not written at the
        # end, so don't expect it in the output.
        self.assertIn(b"history " + expected, output)