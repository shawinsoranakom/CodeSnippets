def test_reports_are_generated(self):
        url = self.live_server_url + "/csp-failure/"
        self.selenium.get(url)
        time.sleep(1)  # Allow time for the CSP report to be sent.
        reports = sorted(
            (r["csp-report"]["document-uri"], r["csp-report"]["violated-directive"])
            for r in csp_reports
        )
        self.assertEqual(reports, [(url, "style-src-elem")])