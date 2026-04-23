def _assert_bytes_received(run: CrawlerRun) -> None:
        assert len(run.bytes) == 9
        for request, data in run.bytes.items():
            joined_data = b"".join(data)
            if run.getpath(request.url) == "/static/":
                assert joined_data == get_testdata("test_site", "index.html")
            elif run.getpath(request.url) == "/static/item1.html":
                assert joined_data == get_testdata("test_site", "item1.html")
            elif run.getpath(request.url) == "/static/item2.html":
                assert joined_data == get_testdata("test_site", "item2.html")
            elif run.getpath(request.url) == "/redirected":
                assert joined_data == b"Redirected here"
            elif run.getpath(request.url) == "/redirect":
                assert (
                    joined_data == b"\n<html>\n"
                    b"    <head>\n"
                    b'        <meta http-equiv="refresh" content="0;URL=/redirected">\n'
                    b"    </head>\n"
                    b'    <body bgcolor="#FFFFFF" text="#000000">\n'
                    b'    <a href="/redirected">click here</a>\n'
                    b"    </body>\n"
                    b"</html>\n"
                )
            elif run.getpath(request.url) == "/static/item999.html":
                assert (
                    joined_data == b"\n<html>\n"
                    b"  <head><title>404 - No Such Resource</title></head>\n"
                    b"  <body>\n"
                    b"    <h1>No Such Resource</h1>\n"
                    b"    <p>File not found.</p>\n"
                    b"  </body>\n"
                    b"</html>\n"
                )
            elif run.getpath(request.url) == "/numbers":
                # signal was fired multiple times
                assert len(data) > 1
                # bytes were received in order
                numbers = [str(x).encode("utf8") for x in range(2**18)]
                assert joined_data == b"".join(numbers)