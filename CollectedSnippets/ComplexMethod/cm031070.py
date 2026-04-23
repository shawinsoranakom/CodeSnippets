def test_full(self):
        for maxsize in [1, 3, 11]:
            with self.subTest(f'maxsize={maxsize}'):
                num_to_add = maxsize
                expected = [False] * (num_to_add * 2 + 3)
                expected[maxsize] = True
                expected[maxsize + 1] = True

                queue = queues.create(maxsize)
                actual = []
                empty = [queue.empty()]

                for _ in range(num_to_add):
                    actual.append(queue.full())
                    queue.put_nowait(None)
                actual.append(queue.full())
                with self.assertRaises(queues.QueueFull):
                    queue.put_nowait(None)
                empty.append(queue.empty())

                for _ in range(num_to_add):
                    actual.append(queue.full())
                    queue.get_nowait()
                actual.append(queue.full())
                with self.assertRaises(queues.QueueEmpty):
                    queue.get_nowait()
                actual.append(queue.full())
                empty.append(queue.empty())

                self.assertEqual(actual, expected)
                self.assertEqual(empty, [True, False, True])

        # no max size
        for args in [(), (0,), (-1,), (-10,)]:
            with self.subTest(f'maxsize={args[0]}' if args else '<default>'):
                num_to_add = 13
                expected = [False] * (num_to_add * 2 + 3)

                queue = queues.create(*args)
                actual = []
                empty = [queue.empty()]

                for _ in range(num_to_add):
                    actual.append(queue.full())
                    queue.put_nowait(None)
                actual.append(queue.full())
                empty.append(queue.empty())

                for _ in range(num_to_add):
                    actual.append(queue.full())
                    queue.get_nowait()
                actual.append(queue.full())
                with self.assertRaises(queues.QueueEmpty):
                    queue.get_nowait()
                actual.append(queue.full())
                empty.append(queue.empty())

                self.assertEqual(actual, expected)
                self.assertEqual(empty, [True, False, True])