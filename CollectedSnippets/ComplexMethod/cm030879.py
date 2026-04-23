def test_rollover_at_midnight(self, weekly=False):
        os_helper.unlink(self.fn)
        now = datetime.datetime.now()
        atTime = now.time()
        if not 0.1 < atTime.microsecond/1e6 < 0.9:
            # The test requires all records to be emitted within
            # the range of the same whole second.
            time.sleep((0.1 - atTime.microsecond/1e6) % 1.0)
            now = datetime.datetime.now()
            atTime = now.time()
        atTime = atTime.replace(microsecond=0)
        fmt = logging.Formatter('%(asctime)s %(message)s')
        when = f'W{now.weekday()}' if weekly else 'MIDNIGHT'
        for i in range(3):
            fh = logging.handlers.TimedRotatingFileHandler(
                self.fn, encoding="utf-8", when=when, atTime=atTime)
            fh.setFormatter(fmt)
            r2 = logging.makeLogRecord({'msg': f'testing1 {i}'})
            fh.emit(r2)
            fh.close()
        self.assertLogFile(self.fn)
        with open(self.fn, encoding="utf-8") as f:
            for i, line in enumerate(f):
                self.assertIn(f'testing1 {i}', line)

        os.utime(self.fn, (now.timestamp() - 1,)*2)
        for i in range(2):
            fh = logging.handlers.TimedRotatingFileHandler(
                self.fn, encoding="utf-8", when=when, atTime=atTime)
            fh.setFormatter(fmt)
            r2 = logging.makeLogRecord({'msg': f'testing2 {i}'})
            fh.emit(r2)
            fh.close()
        rolloverDate = now - datetime.timedelta(days=7 if weekly else 1)
        otherfn = f'{self.fn}.{rolloverDate:%Y-%m-%d}'
        self.assertLogFile(otherfn)
        with open(self.fn, encoding="utf-8") as f:
            for i, line in enumerate(f):
                self.assertIn(f'testing2 {i}', line)
        with open(otherfn, encoding="utf-8") as f:
            for i, line in enumerate(f):
                self.assertIn(f'testing1 {i}', line)