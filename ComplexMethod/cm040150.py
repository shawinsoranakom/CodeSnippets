def test_model_with_input_structure(self, struct_type):
        if backend.backend() == "torch" and struct_type in ("tuple", "dict"):
            self.skipTest("The torch backend doesn't support this structure.")

        class TupleModel(models.Model):
            def call(self, inputs):
                x, y = inputs
                return ops.add(x, y)

        class ArrayModel(models.Model):
            def call(self, inputs):
                x = inputs[0]
                y = inputs[1]
                return ops.add(x, y)

        class DictModel(models.Model):
            def call(self, inputs):
                x = inputs["x"]
                y = inputs["y"]
                return ops.add(x, y)

        batch_size = 3 if backend.backend() != "torch" else 1
        ref_input = np.random.normal(size=(batch_size, 10)).astype("float32")
        if struct_type == "tuple":
            model = TupleModel()
            ref_input = (ref_input, ref_input * 2)
        elif struct_type == "array":
            model = ArrayModel()
            ref_input = [ref_input, ref_input * 2]
        elif struct_type == "dict":
            model = DictModel()
            ref_input = {"x": ref_input, "y": ref_input * 2}

        temp_filepath = os.path.join(self.get_temp_dir(), "exported_model")
        ref_output = model(tree.map_structure(ops.convert_to_tensor, ref_input))

        onnx.export_onnx(model, temp_filepath)
        ort_session = onnxruntime.InferenceSession(temp_filepath)
        if isinstance(ref_input, dict):
            ort_inputs = {
                k.name: v
                for k, v in zip(ort_session.get_inputs(), ref_input.values())
            }
        else:
            ort_inputs = {
                k.name: v for k, v in zip(ort_session.get_inputs(), ref_input)
            }
        self.assertAllClose(ort_session.run(None, ort_inputs)[0], ref_output)

        # Test with keras.saving_lib
        temp_filepath = os.path.join(
            self.get_temp_dir(), "exported_model.keras"
        )
        saving_lib.save_model(model, temp_filepath)
        revived_model = saving_lib.load_model(
            temp_filepath,
            {
                "TupleModel": TupleModel,
                "ArrayModel": ArrayModel,
                "DictModel": DictModel,
            },
        )
        self.assertAllClose(revived_model(ref_input), ref_output)
        temp_filepath = os.path.join(self.get_temp_dir(), "exported_model2")
        onnx.export_onnx(revived_model, temp_filepath)

        # Test with a different batch size
        bigger_ref_input = tree.map_structure(
            lambda x: np.concatenate([x, x], axis=0), ref_input
        )
        if isinstance(bigger_ref_input, dict):
            bigger_ort_inputs = {
                k.name: v
                for k, v in zip(
                    ort_session.get_inputs(), bigger_ref_input.values()
                )
            }
        else:
            bigger_ort_inputs = {
                k.name: v
                for k, v in zip(ort_session.get_inputs(), bigger_ref_input)
            }
        ort_session.run(None, bigger_ort_inputs)