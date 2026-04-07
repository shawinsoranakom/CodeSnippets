def humanize_tester(
        self, test_list, result_list, method, normalize_result_func=escape
    ):
        for test_content, result in zip(test_list, result_list):
            with self.subTest(test_content):
                t = Template("{%% load humanize %%}{{ test_content|%s }}" % method)
                rendered = t.render(Context(locals())).strip()
                self.assertEqual(
                    rendered,
                    normalize_result_func(result),
                    msg="%s test failed, produced '%s', should've produced '%s'"
                    % (method, rendered, result),
                )