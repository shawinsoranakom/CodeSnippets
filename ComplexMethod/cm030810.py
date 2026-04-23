def _check_iteration(self, method, do_keys, do_values, repetitions=10):
        for value in method():
            self.fail("Not empty")
        keys, values = [], []
        for i in range(repetitions):
            keys.append(self._box.add(self._template % i))
            values.append(self._template % i)
        if do_keys and not do_values:
            returned_keys = list(method())
        elif do_values and not do_keys:
            returned_values = list(method())
        else:
            returned_keys, returned_values = [], []
            for key, value in method():
                returned_keys.append(key)
                returned_values.append(value)
        if do_keys:
            self.assertEqual(len(keys), len(returned_keys))
            self.assertEqual(set(keys), set(returned_keys))
        if do_values:
            count = 0
            for value in returned_values:
                self.assertEqual(value['from'], 'foo')
                self.assertLess(int(value.get_payload()), repetitions)
                count += 1
            self.assertEqual(len(values), count)