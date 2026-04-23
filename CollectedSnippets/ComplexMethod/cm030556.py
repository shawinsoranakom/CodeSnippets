def assert_cache_path_exists(self, should_exist=True):
        if self.cache_path:
            if should_exist:
                self.assertTrue(os.path.exists(self.cache_path))
            else:
                self.assertFalse(os.path.exists(self.cache_path))
            return
        cache_dir = os.path.join(self.directory, '__pycache__')
        if not os.path.isdir(cache_dir):
            if should_exist:
                self.fail('no __pycache__ directory exists')
            return
        for f in os.listdir(cache_dir):
            if f.startswith('_test.') and f.endswith('.pyc'):
                if should_exist:
                    return
                self.fail(f'__pycache__/{f} was created')
        else:
            if should_exist:
                self.fail('no __pycache__/_test.*.pyc file exists')