def test_file(self):
        import email.utils
        h = urllib.request.FileHandler()
        o = h.parent = MockOpener()

        TESTFN = os_helper.TESTFN
        towrite = b"hello, world\n"
        canonurl = urllib.request.pathname2url(os.path.abspath(TESTFN), add_scheme=True)
        parsed = urlsplit(canonurl)
        if parsed.netloc:
            raise unittest.SkipTest("non-local working directory")
        urls = [
            canonurl,
            parsed._replace(netloc='localhost').geturl(),
            parsed._replace(netloc=socket.gethostbyname('localhost')).geturl(),
            ]
        try:
            localaddr = socket.gethostbyname(socket.gethostname())
        except socket.gaierror:
            localaddr = ''
        if localaddr:
            urls.append(parsed._replace(netloc=localaddr).geturl())

        for url in urls:
            f = open(TESTFN, "wb")
            try:
                try:
                    f.write(towrite)
                finally:
                    f.close()

                r = h.file_open(Request(url))
                try:
                    data = r.read()
                    headers = r.info()
                    respurl = r.geturl()
                finally:
                    r.close()
                stats = os.stat(TESTFN)
                modified = email.utils.formatdate(stats.st_mtime, usegmt=True)
            finally:
                os.remove(TESTFN)
            self.assertEqual(data, towrite)
            self.assertEqual(headers["Content-type"], "text/plain")
            self.assertEqual(headers["Content-length"], "13")
            self.assertEqual(headers["Last-modified"], modified)
            self.assertEqual(respurl, canonurl)

        for url in [
            parsed._replace(netloc='localhost:80').geturl(),
            "file:///file_does_not_exist.txt",
            "file://not-a-local-host.com//dir/file.txt",
            "file://%s:80%s/%s" % (socket.gethostbyname('localhost'),
                                   os.getcwd(), TESTFN),
            "file://somerandomhost.ontheinternet.com%s/%s" %
            (os.getcwd(), TESTFN),
            ]:
            try:
                f = open(TESTFN, "wb")
                try:
                    f.write(towrite)
                finally:
                    f.close()

                self.assertRaises(urllib.error.URLError,
                                  h.file_open, Request(url))
            finally:
                os.remove(TESTFN)

        h = urllib.request.FileHandler()
        o = h.parent = MockOpener()
        # XXXX why does // mean ftp (and /// mean not ftp!), and where
        #  is file: scheme specified?  I think this is really a bug, and
        #  what was intended was to distinguish between URLs like:
        # file:/blah.txt (a file)
        # file://localhost/blah.txt (a file)
        # file:///blah.txt (a file)
        # file://ftp.example.com/blah.txt (an ftp URL)
        for url, ftp in [
            ("file://ftp.example.com//foo.txt", False),
            ("file://ftp.example.com///foo.txt", False),
            ("file://ftp.example.com/foo.txt", False),
            ("file://somehost//foo/something.txt", False),
            ("file://localhost//foo/something.txt", False),
            ]:
            req = Request(url)
            try:
                h.file_open(req)
            except urllib.error.URLError:
                self.assertFalse(ftp)
            else:
                self.assertIs(o.req, req)
                self.assertEqual(req.type, "ftp")
            self.assertEqual(req.type == "ftp", ftp)