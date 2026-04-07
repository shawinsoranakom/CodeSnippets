def test_directory_security(self):
        with self.source_checker(["/dir1", "/dir2"]) as check_sources:
            check_sources("index.html", ["/dir1/index.html", "/dir2/index.html"])
            check_sources("/etc/passwd", [])
            check_sources("etc/passwd", ["/dir1/etc/passwd", "/dir2/etc/passwd"])
            check_sources("../etc/passwd", [])
            check_sources("../../../etc/passwd", [])
            check_sources("/dir1/index.html", ["/dir1/index.html"])
            check_sources("../dir2/index.html", ["/dir2/index.html"])
            check_sources("/dir1blah", [])
            check_sources("../dir1blah", [])