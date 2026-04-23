def test_builtin_handlers(self):
        # We can't actually *use* too many handlers in the tests,
        # but we can try instantiating them with various options
        if sys.platform in ('linux', 'android', 'darwin'):
            for existing in (True, False):
                fn = make_temp_file()
                if not existing:
                    os.unlink(fn)
                h = logging.handlers.WatchedFileHandler(fn, encoding='utf-8', delay=True)
                if existing:
                    dev, ino = h.dev, h.ino
                    self.assertEqual(dev, -1)
                    self.assertEqual(ino, -1)
                    r = logging.makeLogRecord({'msg': 'Test'})
                    h.handle(r)
                    # Now remove the file.
                    os.unlink(fn)
                    self.assertFalse(os.path.exists(fn))
                    # The next call should recreate the file.
                    h.handle(r)
                    self.assertTrue(os.path.exists(fn))
                else:
                    self.assertEqual(h.dev, -1)
                    self.assertEqual(h.ino, -1)
                h.close()
                if existing:
                    os.unlink(fn)
            if sys.platform == 'darwin':
                sockname = '/var/run/syslog'
            else:
                sockname = '/dev/log'
            try:
                h = logging.handlers.SysLogHandler(sockname)
                self.assertEqual(h.facility, h.LOG_USER)
                self.assertTrue(h.unixsocket)
                h.close()
            except OSError: # syslogd might not be available
                pass
        for method in ('GET', 'POST', 'PUT'):
            if method == 'PUT':
                self.assertRaises(ValueError, logging.handlers.HTTPHandler,
                                  'localhost', '/log', method)
            else:
                h = logging.handlers.HTTPHandler('localhost', '/log', method)
                h.close()
        h = logging.handlers.BufferingHandler(0)
        r = logging.makeLogRecord({})
        self.assertTrue(h.shouldFlush(r))
        h.close()
        h = logging.handlers.BufferingHandler(1)
        self.assertFalse(h.shouldFlush(r))
        h.close()