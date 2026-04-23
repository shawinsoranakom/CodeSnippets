def test_model_with_input_structure(self, struct_type):
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

        batch_size = 3
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

        temp_filepath = os.path.join(self.get_temp_dir(), "exported_model.xml")
        ref_output = model(tree.map_structure(ops.convert_to_tensor, ref_input))

        try:
            openvino.export_openvino(model, temp_filepath)
        except Exception as e:
            if "XlaCallModule" in str(e):
                self.skipTest("OpenVINO does not support XlaCallModule yet")
            raise e

        # Load and run inference with OpenVINO
        core = ov.Core()
        ov_model = core.read_model(temp_filepath)
        compiled_model = core.compile_model(ov_model, "CPU")

        if isinstance(ref_input, dict):
            ov_inputs = [ref_input[key] for key in ref_input.keys()]
        else:
            ov_inputs = list(ref_input)

        ov_output = compiled_model(ov_inputs)[compiled_model.output(0)]
        self.assertAllClose(ov_output, ref_output)

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
        temp_filepath = os.path.join(self.get_temp_dir(), "exported_model2.xml")
        try:
            openvino.export_openvino(revived_model, temp_filepath)
        except Exception as e:
            if "XlaCallModule" in str(e):
                self.skipTest("OpenVINO does not support XlaCallModule yet")
            raise e

        bigger_ref_input = tree.map_structure(
            lambda x: np.concatenate([x, x], axis=0), ref_input
        )
        if isinstance(bigger_ref_input, dict):
            bigger_ov_inputs = [
                bigger_ref_input[key] for key in bigger_ref_input.keys()
            ]
        else:
            bigger_ov_inputs = list(bigger_ref_input)
        compiled_model(bigger_ov_inputs)