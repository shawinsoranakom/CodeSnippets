def test_split_tzname_delta(self):
        tests = [
            ("Asia/Ust+Nera", ("Asia/Ust+Nera", None, None)),
            ("Asia/Ust-Nera", ("Asia/Ust-Nera", None, None)),
            ("Asia/Ust+Nera-02:00", ("Asia/Ust+Nera", "-", "02:00")),
            ("Asia/Ust-Nera+05:00", ("Asia/Ust-Nera", "+", "05:00")),
            ("America/Coral_Harbour-01:00", ("America/Coral_Harbour", "-", "01:00")),
            ("America/Coral_Harbour+02:30", ("America/Coral_Harbour", "+", "02:30")),
            ("UTC+15:00", ("UTC", "+", "15:00")),
            ("UTC-04:43", ("UTC", "-", "04:43")),
            ("UTC", ("UTC", None, None)),
            ("UTC+1", ("UTC+1", None, None)),
        ]
        for tzname, expected in tests:
            with self.subTest(tzname=tzname):
                self.assertEqual(split_tzname_delta(tzname), expected)