def test_unicode_escape_escaping(self):
        test_cases = [
            # Control characters.
            ("line\nbreak", "line\\nbreak"),
            ("carriage\rreturn", "carriage\\rreturn"),
            ("tab\tseparated", "tab\\tseparated"),
            ("formfeed\f", "formfeed\\x0c"),
            ("bell\a", "bell\\x07"),
            ("multi\nline\ntext", "multi\\nline\\ntext"),
            # Slashes.
            ("slash\\test", "slash\\\\test"),
            ("back\\slash", "back\\\\slash"),
            # Quotes.
            ('quote"test"', 'quote"test"'),
            ("quote'test'", "quote'test'"),
            # Accented, composed characters, emojis and symbols.
            ("café", "caf\\xe9"),
            ("e\u0301", "e\\u0301"),  # e + combining acute
            ("smile🙂", "smile\\U0001f642"),
            ("weird ☃️", "weird \\u2603\\ufe0f"),
            # Non-Latin alphabets.
            ("Привет", "\\u041f\\u0440\\u0438\\u0432\\u0435\\u0442"),
            ("你好", "\\u4f60\\u597d"),
            # ANSI escape sequences.
            ("escape\x1b[31mred\x1b[0m", "escape\\x1b[31mred\\x1b[0m"),
            (
                "/\x1b[1;31mCAUTION!!YOU ARE PWNED\x1b[0m/",
                "/\\x1b[1;31mCAUTION!!YOU ARE PWNED\\x1b[0m/",
            ),
            (
                "/\r\n\r\n1984-04-22 INFO    Listening on 0.0.0.0:8080\r\n\r\n",
                "/\\r\\n\\r\\n1984-04-22 INFO    Listening on 0.0.0.0:8080\\r\\n\\r\\n",
            ),
            # Plain safe input.
            ("normal-path", "normal-path"),
            ("slash/colon:", "slash/colon:"),
            # Non strings.
            (0, "0"),
            ([1, 2, 3], "[1, 2, 3]"),
            ({"test": "🙂"}, "{'test': '🙂'}"),
        ]

        msg = "Test message: %s"
        for case, expected in test_cases:
            with (
                self.assertLogs("django.request", level="ERROR") as cm,
                self.subTest(case=case),
            ):
                response = HttpResponse(status=318)
                log_response(msg, case, response=response, level="error")

                record = self.assertLogRecord(
                    cm,
                    msg % expected,
                    levelno=logging.ERROR,
                    status_code=318,
                    request=None,
                )
                # Log record is always a single line.
                self.assertEqual(len(record.getMessage().splitlines()), 1)