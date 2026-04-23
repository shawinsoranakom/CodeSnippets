def test_long_line(self):
        # Bug #20889: long lines trigger newlines to be added to headers
        # (which is not allowed due to bug #10188)
        h = HttpResponse()
        f = b"zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz a\xcc\x88"
        f = f.decode("utf-8")
        h.headers["Content-Disposition"] = 'attachment; filename="%s"' % f
        # This one is triggering https://bugs.python.org/issue20747, that is
        # Python will itself insert a newline in the header
        h.headers["Content-Disposition"] = (
            'attachment; filename="EdelRot_Blu\u0308te (3)-0.JPG"'
        )