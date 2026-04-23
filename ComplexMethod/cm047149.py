def _is_matching(test_filter):
            (tag, module, klass, method, file_path) = test_filter
            if tag and tag not in test_tags:
                return False
            elif file_path and not file_path.endswith(test_module_path):
                return False
            elif not file_path and module and module != test_module:
                return False
            elif klass and klass != test_class:
                return False
            elif method and test_method and method != test_method:
                return False
            return True