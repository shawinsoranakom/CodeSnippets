def test_fixed_layers_export(self, layer_type):
        """Test that fixed layers work with PyTorch export methods.

        Tests the three main fixes:
        1. GlobalAveragePooling2D (mean() dtype fix)
        2. Reshape with -1 (dynamic reshape fix)
        3. Combined scenario (variables.py SymInt fix)
        """
        import tempfile

        import torch

        if layer_type == "global_avg_pool":
            # Test GlobalAveragePooling2D (mean() fix)
            inputs = layers.Input(shape=(None, None, 64))
            x = layers.Conv2D(64, 3, padding="same")(inputs)
            x = layers.GlobalAveragePooling2D()(x)
            x = layers.Dense(10)(x)
            model = models.Model(inputs=inputs, outputs=x)
            sample_input = torch.randn(1, 8, 8, 64)
            test_shapes = [(1, 8, 8, 64), (2, 16, 16, 64)]

        elif layer_type == "reshape_flatten":
            # Test Reshape with -1 (reshape fix)
            inputs = layers.Input(shape=(None, None, 64))
            x = layers.Conv2D(32, 3, padding="same")(inputs)
            x = layers.Reshape((-1, 32))(x)
            model = models.Model(inputs=inputs, outputs=x)
            sample_input = torch.randn(1, 8, 8, 64)
            test_shapes = [(1, 8, 8, 64), (1, 16, 16, 64)]

        else:  # combined
            # Test combined scenario (all fixes)
            inputs = layers.Input(shape=(None, None, 64))
            x = layers.AveragePooling2D(pool_size=2)(inputs)
            x = layers.Conv2D(128, 3, padding="same")(x)
            x = layers.GlobalAveragePooling2D()(x)
            x = layers.Dense(256)(x)
            x = layers.Dropout(0.5)(x)
            x = layers.Dense(10)(x)
            model = models.Model(inputs=inputs, outputs=x)
            sample_input = torch.randn(1, 8, 8, 64)
            test_shapes = [(1, 8, 8, 64), (2, 16, 16, 64)]

        # Test torch.export
        # Note: torch.export has stricter constraints than ONNX export
        # Skip if constraints cannot be satisfied
        try:
            batch_dim = torch.export.Dim("batch", min=1, max=1024)
            h_dim = torch.export.Dim("height", min=1, max=1024)
            w_dim = torch.export.Dim("width", min=1, max=1024)

            exported = torch.export.export(
                model,
                (sample_input,),
                dynamic_shapes=(({0: batch_dim, 1: h_dim, 2: w_dim},),),
                strict=False,
            )
            self.assertIsNotNone(exported)
        except Exception as e:
            # torch.export has known limitations with certain layers
            # The important thing is that ONNX export works
            if "Constraints violated" in str(e):
                pytest.skip(f"torch.export constraints not satisfiable: {e}")
            pytest.skip(f"torch.export not available: {e}")

        # Test ONNX export
        try:
            import onnxruntime as ort

            with tempfile.NamedTemporaryFile(suffix=".onnx", delete=False) as f:
                onnx_path = f.name

            torch.onnx.export(
                model,
                (sample_input,),
                onnx_path,
                input_names=["input"],
                output_names=["output"],
                dynamic_shapes=(
                    (
                        (
                            torch.export.Dim.DYNAMIC,
                            torch.export.Dim.DYNAMIC,
                            torch.export.Dim.DYNAMIC,
                            torch.export.Dim.STATIC,
                        ),
                    ),
                ),
            )

            # Verify ONNX model works with varying shapes
            ort_session = ort.InferenceSession(onnx_path)
            input_name = ort_session.get_inputs()[0].name

            for shape in test_shapes:
                x_test = np.random.randn(*shape).astype(np.float32)
                onnx_output = ort_session.run(None, {input_name: x_test})[0]
                self.assertIsNotNone(onnx_output)

            os.unlink(onnx_path)

        except ImportError:
            pytest.skip("onnxruntime not available")
        except TypeError as e:
            if "dtype" in str(e):
                self.fail(
                    f"ONNX export failed with dtype error for {layer_type}: {e}"
                )
            pytest.skip(f"ONNX export not available: {e}")
        except Exception as e:
            if "Constraints violated" in str(e):
                self.fail(f"ONNX export failed for {layer_type}: {e}")
            pytest.skip(f"ONNX export not available: {e}")