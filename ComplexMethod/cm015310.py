def test_linear_api(self, batch_size, in_features, out_features, use_bias, use_default_observer):
        """test API functionality for nn.quantized.dynamic.Linear"""
        W = torch.rand(out_features, in_features).float()
        qscheme = torch.per_tensor_symmetric if qengine_is_onednn() else torch.per_tensor_affine
        W_scale, W_zp = _calculate_dynamic_qparams(W, torch.qint8, qscheme=qscheme)
        W_q = torch.quantize_per_tensor(W, W_scale, W_zp, torch.qint8)
        X = torch.rand(batch_size, in_features).float()
        B = torch.rand(out_features).float() if use_bias else None
        qlinear = nnqd.Linear(in_features, out_features)
        # Run module with default-initialized parameters.
        # This tests that the constructor is correct.
        qlinear.set_weight_bias(W_q, B)
        qlinear(X)

        # Simple round-trip test to ensure weight()/set_weight() API
        self.assertEqual(qlinear.weight(), W_q)
        W_pack = qlinear._packed_params._packed_params
        Z_dq = qlinear(X)

        # Check if the module implementation matches calling the
        # ops directly
        Z_ref = torch.ops.quantized.linear_dynamic(X, W_pack, reduce_range=True)
        self.assertEqual(Z_ref, Z_dq)

        # Test serialization of dynamic quantized Linear Module using state_dict
        model_dict = qlinear.state_dict()
        b = io.BytesIO()
        torch.save(model_dict, b)
        for weights_only in [True, False]:
            b.seek(0)
            loaded_dict = torch.load(b, weights_only=weights_only)
            for key in model_dict:
                if isinstance(model_dict[key], torch._C.ScriptObject):
                    if not isinstance(loaded_dict[key], torch._C.ScriptObject):
                        raise AssertionError(
                            f"Expected loaded_dict[{key}] to be ScriptObject, got {type(loaded_dict[key])}"
                        )
                    w_model, b_model = torch.ops.quantized.linear_unpack(model_dict[key])
                    w_loaded, b_loaded = torch.ops.quantized.linear_unpack(loaded_dict[key])
                    self.assertEqual(w_model, w_loaded)
                    self.assertEqual(b_model, b_loaded)
                else:
                    self.assertEqual(model_dict[key], loaded_dict[key])
            loaded_qlinear = nnqd.Linear(in_features, out_features)
            loaded_qlinear.load_state_dict(loaded_dict)

            linear_unpack = torch.ops.quantized.linear_unpack
            self.assertEqual(linear_unpack(qlinear._packed_params._packed_params),
                             linear_unpack(loaded_qlinear._packed_params._packed_params))
            if use_bias:
                self.assertEqual(qlinear.bias(), loaded_qlinear.bias())
            self.assertTrue(dir(qlinear) == dir(loaded_qlinear))
            self.assertTrue(hasattr(qlinear, '_packed_params'))
            self.assertTrue(hasattr(loaded_qlinear, '_packed_params'))
            self.assertTrue(hasattr(qlinear, '_weight_bias'))
            self.assertTrue(hasattr(loaded_qlinear, '_weight_bias'))

            self.assertEqual(qlinear._weight_bias(), loaded_qlinear._weight_bias())
            self.assertEqual(qlinear._weight_bias(), torch.ops.quantized.linear_unpack(qlinear._packed_params._packed_params))
            Z_dq2 = qlinear(X)
            self.assertEqual(Z_dq, Z_dq2)

        b = io.BytesIO()
        torch.save(qlinear, b)
        b.seek(0)
        # weights_only=False as this is legacy code that saves the model
        loaded = torch.load(b, weights_only=False)
        self.assertEqual(qlinear.weight(), loaded.weight())
        self.assertEqual(qlinear.zero_point, loaded.zero_point)

        # Test JIT
        self.checkScriptable(qlinear, [[X]], check_save_load=True)

        modules_under_test = [torch.nn.Linear, torch.nn.modules.linear.NonDynamicallyQuantizableLinear]
        for mut in modules_under_test:
            # Test from_float
            float_linear = mut(in_features, out_features).float()
            if use_default_observer:
                float_linear.qconfig = torch.ao.quantization.default_dynamic_qconfig
            prepare_dynamic(float_linear)
            float_linear(X.float())
            quantized_float_linear = nnqd.Linear.from_float(float_linear)

            # Smoke test to make sure the module actually runs
            quantized_float_linear(X)

        # Smoke test extra_repr
        self.assertTrue('QuantizedLinear' in str(quantized_float_linear))