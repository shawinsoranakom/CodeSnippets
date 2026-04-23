def test_case_sensitivity(self):
        with self.source_checker(["/dir1", "/DIR2"]) as check_sources:
            check_sources("index.html", ["/dir1/index.html", "/DIR2/index.html"])
            check_sources("/DIR1/index.HTML", ["/DIR1/index.HTML"])