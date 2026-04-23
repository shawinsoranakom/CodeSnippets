def _test_linear_api_impl(self, qlinear_module, module_name, qlinear_op,
                              batch_size, in_features, out_features, use_bias,
                              per_channel, **post_ops_kwargs):
        if torch.backends.quantized.engine == 'qnnpack':
            per_channel = False

        W = torch.rand(out_features, in_features).float()
        if per_channel:
            scale_tensor = torch.ones(out_features, dtype=torch.double)
            zero_point_tensor = torch.zeros(out_features, dtype=torch.long)
            for i in range(len(scale_tensor)):
                scale_tensor[i] = (i + 1.0) / 255.0
            W_q = torch.quantize_per_channel(W, scales=scale_tensor,
                                             zero_points=zero_point_tensor,
                                             axis=0, dtype=torch.qint8)
        else:
            # ONEDNN only supports symmetric quantization of weight
            W_zp = 0 if qengine_is_onednn() else 4
            W_q = torch.quantize_per_tensor(W, 0.1, W_zp, torch.qint8)

        X = torch.rand(batch_size, in_features).float()
        X_q = torch.quantize_per_tensor(X, 0.2, 10, torch.quint8)
        B = torch.rand(out_features).float() if use_bias else None
        scale = 0.5
        zero_point = 3
        qlinear = qlinear_module(in_features, out_features, **post_ops_kwargs)

        qlinear_copy = copy.deepcopy(qlinear)
        # set random quantized weight and bias before test torch scriptable
        qlinear_copy.set_weight_bias(W_q, B)
        self.checkScriptable(qlinear_copy, [[X_q]], check_save_load=True)
        # Run module with default-initialized parameters.
        # This tests that the constructor is correct.
        qlinear(X_q)

        qlinear.set_weight_bias(W_q, B)
        # Simple round-trip test to ensure weight()/set_weight() API
        self.assertEqual(qlinear.weight(), W_q, atol=1e-5, rtol=0)

        # testing packed param implementation
        qlinear.scale = float(scale)
        qlinear.zero_point = int(zero_point)
        Z_q = qlinear(X_q)

        # Check if the module implementation matches calling the
        # ops directly
        W_pack = qlinear._packed_params._packed_params
        Z_ref = qlinear_op(X_q, W_pack, scale, zero_point, **post_ops_kwargs)

        self.assertEqual(Z_ref, Z_q)
        self.assertTrue(module_name in str(qlinear))

        # Test serialization of quantized Linear Module using state_dict
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

            loaded_qlinear = qlinear_module(
                in_features, out_features, **post_ops_kwargs)
            loaded_qlinear.load_state_dict(loaded_dict)
            linear_unpack = torch.ops.quantized.linear_unpack
            self.assertEqual(linear_unpack(qlinear._packed_params._packed_params),
                             linear_unpack(loaded_qlinear._packed_params._packed_params))
            self.assertEqual(qlinear.scale, loaded_qlinear.scale)
            self.assertEqual(qlinear.zero_point, loaded_qlinear.zero_point)
            # scripting will add __overloads__ to __dict__, which is why we script a copy
            # to be able to do the check in the next line
            self.checkScriptable(copy.deepcopy(loaded_qlinear), [[X_q]], check_save_load=True)
            self.assertTrue(dir(qlinear) == dir(loaded_qlinear))
            self.assertEqual(qlinear._weight_bias(), loaded_qlinear._weight_bias())
            self.assertEqual(qlinear._weight_bias(), torch.ops.quantized.linear_unpack(qlinear._packed_params._packed_params))
            Z_q2 = loaded_qlinear(X_q)
            self.assertEqual(Z_q, Z_q2)

        # Test serialization
        b = io.BytesIO()
        torch.save(qlinear, b)
        b.seek(0)
        # weights_only=False as this is legacy code that saves the model
        loaded = torch.load(b, weights_only=False)
        self.assertEqual(qlinear.weight(), loaded.weight())
        self.assertEqual(qlinear.scale, loaded.scale)
        self.assertEqual(qlinear.zero_point, loaded.zero_point)

        # Test torch.package
        buffer = io.BytesIO()
        with PackageExporter(buffer) as pe:
            pe.save_pickle("module", "qlinear.pkl", qlinear)
        buffer.seek(0)

        importer = PackageImporter(buffer)
        loaded_from_package = importer.load_pickle("module", "qlinear.pkl")
        self.assertEqual(qlinear.weight(), loaded_from_package.weight())
        self.assertEqual(qlinear.scale, loaded_from_package.scale)
        self.assertEqual(qlinear.zero_point, loaded_from_package.zero_point)

        for name, _ in loaded_from_package.named_modules():
            # noop, just make sure attribute "_modules" is restored correctly during torch.package import
            if name is None:
                raise AssertionError("name is None")

        # Test copy and deepcopy
        copied_linear = copy.copy(qlinear)
        self.assertEqual(copied_linear.bias(), qlinear.bias())
        self.assertEqual(copied_linear.scale, qlinear.scale)
        self.assertEqual(copied_linear.zero_point,
                         qlinear.zero_point)
        Y_copied = copied_linear(X_q)
        np.testing.assert_array_almost_equal(
            Z_q.int_repr().numpy(), Y_copied.int_repr().numpy(), decimal=0)

        deepcopied_linear = copy.deepcopy(qlinear)
        self.assertEqual(deepcopied_linear.bias(), qlinear.bias())
        self.assertEqual(deepcopied_linear.scale, qlinear.scale)
        self.assertEqual(deepcopied_linear.zero_point,
                         qlinear.zero_point)
        Y_deepcopied = copied_linear(X_q)
        np.testing.assert_array_almost_equal(
            Z_q.int_repr().numpy(), Y_deepcopied.int_repr().numpy(), decimal=0)

        # Test JIT
        self.checkScriptable(qlinear, [[X_q]], check_save_load=True)

        # Make sure `from_float` works for all linear variants
        modules_under_test = [torch.nn.Linear, torch.nn.modules.linear.NonDynamicallyQuantizableLinear]

        for mut in modules_under_test:
            # Test from_float.
            float_linear = mut(in_features, out_features).float()
            float_linear.qconfig = torch.ao.quantization.default_qconfig
            torch.ao.quantization.prepare(float_linear, inplace=True)
            float_linear(X.float())
            # Sequential allows swapping using "convert".
            quantized_float_linear = torch.nn.Sequential(float_linear)
            quantized_float_linear = torch.ao.quantization.convert(quantized_float_linear, inplace=True)

            # Smoke test to make sure the module actually runs
            quantized_float_linear(X_q)

            # Smoke test extra_repr
            self.assertTrue('QuantizedLinear' in str(quantized_float_linear))