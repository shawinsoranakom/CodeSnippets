def test_compute_rollover_weekly_attime(self):
        currentTime = int(time.time())
        today = currentTime - currentTime % 86400

        atTime = datetime.time(12, 0, 0)

        wday = time.gmtime(today).tm_wday
        for day in range(7):
            rh = logging.handlers.TimedRotatingFileHandler(
                self.fn, encoding="utf-8", when='W%d' % day, interval=1, backupCount=0,
                utc=True, atTime=atTime)
            try:
                if wday > day:
                    # The rollover day has already passed this week, so we
                    # go over into next week
                    expected = (7 - wday + day)
                else:
                    expected = (day - wday)
                # At this point expected is in days from now, convert to seconds
                expected *= 24 * 60 * 60
                # Add in the rollover time
                expected += 12 * 60 * 60
                # Add in adjustment for today
                expected += today

                actual = rh.computeRollover(today)
                if actual != expected:
                    print('failed in timezone: %d' % time.timezone)
                    print('local vars: %s' % locals())
                self.assertEqual(actual, expected)

                actual = rh.computeRollover(today + 12 * 60 * 60 - 1)
                if actual != expected:
                    print('failed in timezone: %d' % time.timezone)
                    print('local vars: %s' % locals())
                self.assertEqual(actual, expected)

                if day == wday:
                    # goes into following week
                    expected += 7 * 24 * 60 * 60
                actual = rh.computeRollover(today + 12 * 60 * 60)
                if actual != expected:
                    print('failed in timezone: %d' % time.timezone)
                    print('local vars: %s' % locals())
                self.assertEqual(actual, expected)

                actual = rh.computeRollover(today + 13 * 60 * 60)
                if actual != expected:
                    print('failed in timezone: %d' % time.timezone)
                    print('local vars: %s' % locals())
                self.assertEqual(actual, expected)
            finally:
                rh.close()