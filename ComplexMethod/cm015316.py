def _test_match_shadow_activations(
        self, m, data, prepared_expected_node_occurrence=None, results_len=None,
        should_log_inputs=False, qconfig_dict=None, skip_scripting=False,
        prepare_fn=prepare_fx, compare_fp32_vs_fp32_prepared=True,
    ):
        if qconfig_dict is None:
            qconfig_dict = torch.ao.quantization.get_default_qconfig_mapping()
        if prepare_fn is prepare_fx:
            m.eval()
        else:
            m.train()
        print("qconfig_dict:", qconfig_dict)
        mp = prepare_fn(copy.deepcopy(m), qconfig_dict, example_inputs=data)
        print("prepared:", mp)
        mp(*data)
        mp_copy = copy.deepcopy(mp)
        mq = convert_fx(mp_copy)
        print("quantized:", mq)

        if compare_fp32_vs_fp32_prepared:
            m_shadows_mp = add_shadow_loggers(
                'a', copy.deepcopy(m), 'b', copy.deepcopy(mp),
                OutputLogger, should_log_inputs=should_log_inputs)
        mp_shadows_mq = add_shadow_loggers(
            'a', mp, 'b', mq, OutputLogger,
            should_log_inputs=should_log_inputs)

        if prepared_expected_node_occurrence:
            if compare_fp32_vs_fp32_prepared:
                self.checkGraphModuleNodes(
                    m_shadows_mp, expected_node_occurrence=prepared_expected_node_occurrence)
            self.checkGraphModuleNodes(
                mp_shadows_mq, expected_node_occurrence=prepared_expected_node_occurrence)

        if not skip_scripting:
            if compare_fp32_vs_fp32_prepared:
                m_shadows_mp = torch.jit.script(m_shadows_mp)
            mp_shadows_mq = torch.jit.script(mp_shadows_mq)

        # calibrate
        if compare_fp32_vs_fp32_prepared:
            m_shadows_mp(*data)
        mp_shadows_mq(*data)

        # check activation result correctness
        results = []
        models = (m_shadows_mp, mp_shadows_mq) if \
            compare_fp32_vs_fp32_prepared else (mp_shadows_mq,)
        for model in models:
            act_compare_dict = extract_shadow_logger_info(
                model, OutputLogger, 'b')
            if results_len is not None:
                self.assertTrue(
                    len(act_compare_dict) == results_len,
                    f"expected len {results_len}, got len {len(act_compare_dict)}")
            self.assert_ns_compare_dict_valid(act_compare_dict)
            extend_logger_results_with_comparison(
                act_compare_dict, 'a', 'b', compute_sqnr, 'sqnr')
            extend_logger_results_with_comparison(
                act_compare_dict, 'a', 'b', compute_normalized_l2_error, 'l2_error')
            extend_logger_results_with_comparison(
                act_compare_dict, 'a', 'b', compute_cosine_similarity,
                'cosine_similarity')
            results.append(act_compare_dict)
        return results