def run_all_tests(self) -> Dict[str, Dict[str, Any]]:
        """Run comprehensive test suite across all sizes and types."""
        all_results = {}

        for size in self.sizes:
            size_key = f"{size / (1 << 20):.2f}MB"
            all_results[size_key] = {}

            # Test 1: Large bytes object (BINBYTES8)
            test_name = f"bytes_{size_key}"
            obj = DataGenerator.large_bytes(size)
            all_results[size_key][test_name] = self.run_test(test_name, obj)

            # Test 2: Large ASCII string (BINUNICODE8)
            test_name = f"string_ascii_{size_key}"
            obj = DataGenerator.large_string_ascii(size)
            all_results[size_key][test_name] = self.run_test(test_name, obj)

            # Test 3: Large multibyte UTF-8 string
            if size >= 3:
                test_name = f"string_utf8_{size_key}"
                obj = DataGenerator.large_string_multibyte(size)
                all_results[size_key][test_name] = self.run_test(test_name, obj)

            # Test 4: Large bytearray (BYTEARRAY8, protocol 5)
            if self.protocol >= 5:
                test_name = f"bytearray_{size_key}"
                obj = DataGenerator.large_bytearray(size)
                all_results[size_key][test_name] = self.run_test(test_name, obj)

            # Test 5: List of large objects (repeated chunking)
            if size >= MIN_READ_BUF_SIZE * 2:
                test_name = f"list_large_items_{size_key}"
                item_size = size // 5
                obj = DataGenerator.list_of_large_bytes(item_size, 5)
                all_results[size_key][test_name] = self.run_test(test_name, obj)

            # Test 6: Dict with large values
            if size >= MIN_READ_BUF_SIZE * 2:
                test_name = f"dict_large_values_{size_key}"
                value_size = size // 3
                obj = DataGenerator.dict_with_large_values(value_size, 3)
                all_results[size_key][test_name] = self.run_test(test_name, obj)

            # Test 7: Nested structure
            if size >= MIN_READ_BUF_SIZE:
                test_name = f"nested_{size_key}"
                obj = DataGenerator.nested_structure(size)
                all_results[size_key][test_name] = self.run_test(test_name, obj)

            # Test 8: Tuple (immutable)
            if size >= 3:
                test_name = f"tuple_{size_key}"
                obj = DataGenerator.tuple_of_large_objects(size)
                all_results[size_key][test_name] = self.run_test(test_name, obj)

        return all_results