def test_BoundedSemaphore_limit(self):
        # BoundedSemaphore should raise ValueError if released too often.
        for limit in range(1, 10):
            bs = threading.BoundedSemaphore(limit)
            threads = [threading.Thread(target=bs.acquire)
                       for _ in range(limit)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
            threads = [threading.Thread(target=bs.release)
                       for _ in range(limit)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
            self.assertRaises(ValueError, bs.release)