def test_layer_variable_tracking_correct(self):
        class TrainingLayer(layers.Layer):
            def __init__(self):
                super().__init__()
                self.post_build_modify_layer = PostBuildModifyLayer()

            def call(self, input):
                return self.post_build_modify_layer(input)

        class PostBuildModifyLayer(layers.Layer):
            def call(self, input):
                return self.var + input

            def build(self, _):
                self.var = self.add_weight(
                    shape=(2,),
                    name="var",
                )

            def post_build_add(self):
                self._tracker.unlock()
                self.additional_var = self.add_weight(
                    shape=(2,),
                    name="var2",
                )
                self._tracker.lock()

            def post_build_remove(self):
                self._tracker.unlock()
                self._untrack_variable(self.var)
                del self.var
                self._tracker.lock()

        layer = TrainingLayer()
        output = layer(backend.KerasTensor((4, 2)))

        self.assertEqual(output.shape, (4, 2))
        self.assertEqual(len(layer.variables), 1)
        self.assertEqual(
            layer.variables[0].path,
            "training_layer/post_build_modify_layer/var",
        )
        if backend.backend() == "torch":
            parameter_names = [pname for pname, _ in layer.named_parameters()]
            self.assertEqual(len(parameter_names), 1)
            self.assertEqual(
                parameter_names[0],
                "_torch_params.training_layer/post_build_modify_layer/var",
            )

        layer.post_build_modify_layer.post_build_add()
        self.assertEqual(len(layer.variables), 2)
        self.assertEqual(
            layer.variables[0].path,
            "training_layer/post_build_modify_layer/var",
        )
        self.assertEqual(
            layer.variables[1].path,
            "training_layer/post_build_modify_layer/var2",
        )
        if backend.backend() == "torch":
            # TODO (haohuanw, fchollet): Needs further discussion on how to
            # properly manage torch params. Post build modification cannot
            # propagate to parent torch params.
            parameter_names = [pname for pname, _ in layer.named_parameters()]
            # Below check should have 2 parameters instead of 1.
            self.assertEqual(len(parameter_names), 1)
            self.assertEqual(
                parameter_names[0],
                "_torch_params.training_layer/post_build_modify_layer/var",
            )

            parameter_names = [
                pname
                for pname, _ in layer.post_build_modify_layer.named_parameters()
            ]
            self.assertEqual(len(parameter_names), 2)
            self.assertEqual(
                parameter_names[0],
                "_torch_params.training_layer/post_build_modify_layer/var",
            )
            self.assertEqual(
                parameter_names[1],
                "_torch_params.training_layer/post_build_modify_layer/var2",
            )

        layer.post_build_modify_layer.post_build_remove()
        self.assertEqual(len(layer.variables), 1)
        self.assertEqual(
            layer.variables[0].path,
            "training_layer/post_build_modify_layer/var2",
        )
        if backend.backend() == "torch":
            # TODO (haohuanw, fchollet): Needs further discussion on how to
            # properly manage torch params. Post build modification cannot
            # propagate to parent torch params.
            parameter_names = [pname for pname, _ in layer.named_parameters()]
            # Below check should have 1 parameters instead of 2, torch_params
            # in parent layer is wrong.
            self.assertEqual(len(parameter_names), 2)
            self.assertEqual(
                parameter_names[0],
                "post_build_modify_layer._torch_params.training_layer/"
                "post_build_modify_layer/var2",
            )
            self.assertEqual(
                parameter_names[1],
                "_torch_params.training_layer/post_build_modify_layer/var",
            )

            parameter_names = [
                pname
                for pname, _ in layer.post_build_modify_layer.named_parameters()
            ]
            self.assertEqual(len(parameter_names), 1)
            self.assertEqual(
                parameter_names[0],
                "_torch_params.training_layer/post_build_modify_layer/var2",
            )