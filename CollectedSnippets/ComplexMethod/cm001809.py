def test_galore_matched_modules(self):
        regex_patterns = [r".*.attn.*", r".*.mlp.*"]

        module_names = [
            "model.transformer.h.0.ln_1",
            "model.transformer.h.0.attn.q_proj",
            "model.lm_head",
            "model.transformer.h.0.mlp.up_proj",
        ]
        expected_values = [False, True, False, True]

        for expected_value, module_name in zip(expected_values, module_names):
            is_module_matched, is_regex = check_target_module_exists(regex_patterns, module_name, return_is_regex=True)
            self.assertTrue(is_module_matched == expected_value)
            if is_module_matched:
                self.assertTrue(is_regex)

        exact_patterns = ["q_proj", "up_proj"]

        module_names = [
            "model.transformer.h.0.ln_1",
            "model.transformer.h.0.attn.q_proj",
            "model.lm_head",
            "model.transformer.h.0.mlp.up_proj",
        ]
        expected_values = [False, True, False, True]

        for expected_value, module_name in zip(expected_values, module_names):
            is_module_matched, is_regex = check_target_module_exists(exact_patterns, module_name, return_is_regex=True)
            self.assertTrue(is_module_matched == expected_value)
            if is_module_matched:
                self.assertFalse(is_regex)

        simple_regex = r".*.attn.*"

        module_names = [
            "model.transformer.h.0.ln_1",
            "model.transformer.h.0.attn.q_proj",
            "model.lm_head",
            "model.transformer.h.0.mlp.up_proj",
        ]
        expected_values = [False, True, False, False]

        for expected_value, module_name in zip(expected_values, module_names):
            is_module_matched, is_regex = check_target_module_exists(simple_regex, module_name, return_is_regex=True)
            self.assertTrue(is_module_matched == expected_value)
            if is_module_matched:
                self.assertTrue(is_regex)

        simple_regex = "model.transformer.h.0.attn.q_proj"

        module_names = [
            "model.transformer.h.0.ln_1",
            "model.transformer.h.0.attn.q_proj",
            "model.lm_head",
            "model.transformer.h.0.mlp.up_proj",
        ]
        expected_values = [False, True, False, False]

        for expected_value, module_name in zip(expected_values, module_names):
            is_module_matched, is_regex = check_target_module_exists(simple_regex, module_name, return_is_regex=True)
            self.assertTrue(is_module_matched == expected_value)
            if is_module_matched:
                self.assertFalse(is_regex)

        target_modules = ["attn", "mlp"]

        module_names = [
            "model.transformer.h.0.ln_1",
            "model.transformer.h.0.attn.q_proj",
            "model.lm_head",
            "model.transformer.h.0.mlp.up_proj",
        ]
        expected_values = [False, True, False, True]

        for expected_value, module_name in zip(expected_values, module_names):
            is_module_matched, is_regex = check_target_module_exists(target_modules, module_name, return_is_regex=True)
            self.assertTrue(is_module_matched == expected_value)
            if is_module_matched:
                self.assertFalse(is_regex)