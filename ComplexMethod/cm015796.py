def test_combo_async_concurrent(
        self: Self,
        async_cache_type: type[icache.AsyncCache],
        key_type: type[icache.Key],
        value_type: type[icache.Value],
        get_first: bool,
    ) -> None:
        # Tests a mix of concurrent asynchronous get and insert operations, with the order
        # of operations varied by the get_first parameter, to ensure correctness under
        # interleaved async access.
        if not self.cache_type_supports_key_and_value_types(
            async_cache_type, key_type, value_type
        ):
            return

        executor, iters = ThreadPoolExecutor(), 50

        async_cache: icache.AsyncCache = async_cache_type()
        self.maybe_randomize_base_dir(async_cache)
        keys = self.keys_not_in(async_cache, lambda: self.key(key_type), iters) * 2
        values = self.values_unalike(lambda: self.value(value_type), iters * 2)

        for key in keys:
            self.assertIsNone(async_cache.get(key))

        get_futures, insert_futures = [], []
        for key, value in zip(keys, values):
            if get_first:
                get_futures.append(async_cache.get_async(key, executor))
                insert_futures.append(async_cache.insert_async(key, value, executor))
            else:
                insert_futures.append(async_cache.insert_async(key, value, executor))
                get_futures.append(async_cache.get_async(key, executor))

        inserted = {}
        for key, value, get_future, insert_future in zip(
            keys, values, get_futures, insert_futures
        ):
            if (get := get_future.result()) is not None:
                if insert_future.result():
                    self.assertEqual(get, value)
                    self.assertTrue(key not in inserted)
                    inserted[key] = value
            else:
                if insert_future.result():
                    self.assertTrue(key not in inserted)
                    inserted[key] = value

        self.assertTrue(set(keys) == set(inserted.keys()))
        for key, value in inserted.items():
            self.assertEqual(async_cache.get(key), value)

        executor.shutdown()