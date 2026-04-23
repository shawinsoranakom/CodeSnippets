def test_input_weight_equalization_activation_values(self):
        """ After applying the equalization functions check if the input
        observer's min/max values are as expected
        """

        tests = [SingleLayerLinearModel, TwoLayerLinearModel, SingleLayerFunctionalLinearModel]

        x = torch.rand((5, 5))
        torch.manual_seed(0)
        for M in tests:
            m = M().eval()
            exp_eq_scales = self.get_expected_eq_scales(m, x.detach().numpy())
            exp_weights, exp_bias = self.get_expected_weights_bias(m, x.detach().numpy(), exp_eq_scales)
            exp_inp_act_vals = self.get_expected_inp_act_vals(m, x, exp_eq_scales, exp_weights, exp_bias)
            exp_weight_act_vals = self.get_expected_weight_act_vals(exp_weights)

            example_inputs = (x,)
            prepared = prepare_fx(
                m, specific_qconfig_dict,
                example_inputs=example_inputs,
                _equalization_config=default_equalization_qconfig_dict)
            prepared(x)
            convert_ref = _convert_equalization_ref(prepared)
            convert_ref(x)

            modules = dict(convert_ref.named_modules(remove_duplicate=False))
            inp_counter = 0
            weight_counter = 0
            for node in convert_ref.graph.nodes:
                users = list(node.users)
                if node.op == 'call_module' and isinstance(modules[str(node.target)], MinMaxObserver):
                    if len(users) == 1 and users[0].target == torch.nn.functional.linear and users[0].args[1] == node:
                        # Check min/max values of weight activation layers
                        exp_min_val, exp_max_val = exp_weight_act_vals[weight_counter]
                        self.assertEqual(modules[str(node.target)].min_val, exp_min_val)
                        self.assertEqual(modules[str(node.target)].max_val, exp_max_val)
                        weight_counter += 1
                    else:
                        # Check min/max values of input activation layers
                        exp_min_val, exp_max_val = exp_inp_act_vals[inp_counter]
                        self.assertEqual(modules[str(node.target)].min_val, exp_min_val)
                        self.assertEqual(modules[str(node.target)].max_val, exp_max_val)
                        inp_counter += 1