def run_layer_test(
        self,
        layer_cls,
        init_kwargs,
        input_shape=None,
        input_dtype=None,
        input_sparse=False,
        input_ragged=False,
        input_data=None,
        call_kwargs=None,
        expected_output_shape=None,
        expected_output_dtype=None,
        expected_output_sparse=False,
        expected_output_ragged=False,
        expected_output=None,
        expected_num_trainable_weights=None,
        expected_num_non_trainable_weights=None,
        expected_num_non_trainable_variables=None,
        expected_num_seed_generators=None,
        expected_num_losses=None,
        supports_masking=None,
        expected_mask_shape=None,
        custom_objects=None,
        run_training_check=True,
        run_mixed_precision_check=True,
        assert_built_after_instantiation=False,
        tpu_atol=None,
        tpu_rtol=None,
    ):
        """Run basic checks on a layer.

        Args:
            layer_cls: The class of the layer to test.
            init_kwargs: Dict of arguments to be used to
                instantiate the layer.
            input_shape: Shape tuple (or list/dict of shape tuples)
                to call the layer on.
            input_dtype: Corresponding input dtype.
            input_sparse: Whether the input is a sparse tensor (this requires
                the backend to support sparse tensors).
            input_ragged: Whether the input is a ragged tensor (this requires
                the backend to support ragged tensors).
            input_data: Tensor (or list/dict of tensors)
                to call the layer on.
            call_kwargs: Dict of arguments to use when calling the
                layer (does not include the first input tensor argument)
            expected_output_shape: Shape tuple
                (or list/dict of shape tuples)
                expected as output.
            expected_output_dtype: dtype expected as output.
            expected_output_sparse: Whether the output is expected to be sparse
                (this requires the backend to support sparse tensors).
            expected_output_ragged: Whether the output is expected to be ragged
                (this requires the backend to support ragged tensors).
            expected_output: Expected output tensor -- only
                to be specified if input_data is provided.
            expected_num_trainable_weights: Expected number
                of trainable weights of the layer once built.
            expected_num_non_trainable_weights: Expected number
                of non-trainable weights of the layer once built.
            expected_num_seed_generators: Expected number of
                SeedGenerators objects of the layer once built.
            expected_num_losses: Expected number of loss tensors
                produced when calling the layer.
            supports_masking: If True, will check that the layer
                supports masking.
            expected_mask_shape: Expected mask shape tuple
                returned by compute_mask() (only supports 1 shape).
            custom_objects: Dict of any custom objects to be
                considered during deserialization.
            run_training_check: Whether to attempt to train the layer
                (if an input shape or input data was provided).
            run_mixed_precision_check: Whether to test the layer with a mixed
                precision dtype policy.
            assert_built_after_instantiation: Whether to assert `built=True`
                after the layer's instantiation.
        """
        if input_shape is not None and input_data is not None:
            raise ValueError(
                "input_shape and input_data cannot be passed at the same time."
            )
        if expected_output_shape is not None and expected_output is not None:
            raise ValueError(
                "expected_output_shape and expected_output cannot be passed "
                "at the same time."
            )
        if expected_output is not None and input_data is None:
            raise ValueError(
                "In order to use expected_output, input_data must be provided."
            )
        if expected_mask_shape is not None and supports_masking is not True:
            raise ValueError(
                "In order to use expected_mask_shape, supports_masking "
                "must be True."
            )

        init_kwargs = init_kwargs or {}
        call_kwargs = call_kwargs or {}

        if input_shape is not None and input_dtype is not None:
            if isinstance(input_shape, tuple) and is_shape_tuple(
                input_shape[0]
            ):
                self.assertIsInstance(input_dtype, tuple)
                self.assertEqual(
                    len(input_shape),
                    len(input_dtype),
                    msg="The number of input shapes and dtypes does not match",
                )
            elif isinstance(input_shape, dict):
                self.assertIsInstance(input_dtype, dict)
                self.assertEqual(
                    set(input_shape.keys()),
                    set(input_dtype.keys()),
                    msg="The number of input shapes and dtypes does not match",
                )
            elif isinstance(input_shape, list):
                self.assertIsInstance(input_dtype, list)
                self.assertEqual(
                    len(input_shape),
                    len(input_dtype),
                    msg="The number of input shapes and dtypes does not match",
                )
            elif not isinstance(input_shape, tuple):
                raise ValueError("The type of input_shape is not supported")
        if input_shape is not None and input_dtype is None:
            input_dtype = tree.map_shape_structure(
                lambda _: "float32", input_shape
            )

        # Estimate actual number of weights, variables, seed generators if
        # expected ones not set. When using layers uses composition it should
        # build each sublayer manually.
        if input_data is not None or input_shape is not None:
            if input_data is None:
                input_data = create_eager_tensors(
                    input_shape, input_dtype, input_sparse, input_ragged
                )
            layer = layer_cls(**init_kwargs)
            if isinstance(input_data, dict):
                layer(**input_data, **call_kwargs)
            else:
                layer(input_data, **call_kwargs)

            if expected_num_trainable_weights is None:
                expected_num_trainable_weights = len(layer.trainable_weights)
            if expected_num_non_trainable_weights is None:
                expected_num_non_trainable_weights = len(
                    layer.non_trainable_weights
                )
            if expected_num_non_trainable_variables is None:
                expected_num_non_trainable_variables = len(
                    layer.non_trainable_variables
                )
            if expected_num_seed_generators is None:
                expected_num_seed_generators = len(get_seed_generators(layer))

        # Serialization test.
        layer = layer_cls(**init_kwargs)
        self.run_class_serialization_test(layer, custom_objects)

        # Basic masking test.
        if supports_masking is not None:
            self.assertEqual(
                layer.supports_masking,
                supports_masking,
                msg="Unexpected supports_masking value",
            )

        def run_build_asserts(layer):
            self.assertTrue(layer.built)
            if expected_num_trainable_weights is not None:
                self.assertLen(
                    layer.trainable_weights,
                    expected_num_trainable_weights,
                    msg="Unexpected number of trainable_weights",
                )
            if expected_num_non_trainable_weights is not None:
                self.assertLen(
                    layer.non_trainable_weights,
                    expected_num_non_trainable_weights,
                    msg="Unexpected number of non_trainable_weights",
                )
            if expected_num_non_trainable_variables is not None:
                self.assertLen(
                    layer.non_trainable_variables,
                    expected_num_non_trainable_variables,
                    msg="Unexpected number of non_trainable_variables",
                )
            if expected_num_seed_generators is not None:
                self.assertLen(
                    get_seed_generators(layer),
                    expected_num_seed_generators,
                    msg="Unexpected number of seed_generators",
                )
            if (
                backend.backend() == "torch"
                and expected_num_trainable_weights is not None
                and expected_num_non_trainable_weights is not None
                and expected_num_seed_generators is not None
            ):
                self.assertLen(
                    layer.torch_params,
                    expected_num_trainable_weights
                    + expected_num_non_trainable_weights
                    + expected_num_seed_generators,
                    msg="Unexpected number of torch_params",
                )

        def run_output_asserts(
            layer, output, eager=False, tpu_atol=None, tpu_rtol=None
        ):
            if expected_output_shape is not None:

                def verify_shape(expected_shape, x):
                    shape = x.shape
                    if len(shape) != len(expected_shape):
                        return False
                    for expected_dim, dim in zip(expected_shape, shape):
                        if expected_dim is not None and expected_dim != dim:
                            return False
                    return True

                shapes_match = tree.map_structure_up_to(
                    output, verify_shape, expected_output_shape, output
                )
                self.assertTrue(
                    all(tree.flatten(shapes_match)),
                    msg=f"Expected output shapes {expected_output_shape} but "
                    f"received {tree.map_structure(lambda x: x.shape, output)}",
                )
            if expected_output_dtype is not None:

                def verify_dtype(expected_dtype, x):
                    return expected_dtype == backend.standardize_dtype(x.dtype)

                dtypes_match = tree.map_structure(
                    verify_dtype, expected_output_dtype, output
                )
                self.assertTrue(
                    all(tree.flatten(dtypes_match)),
                    msg=f"Expected output dtypes {expected_output_dtype} but "
                    f"received {tree.map_structure(lambda x: x.dtype, output)}",
                )
            if expected_output_sparse:
                for x in tree.flatten(output):
                    self.assertSparse(x)
            if expected_output_ragged:
                for x in tree.flatten(output):
                    self.assertRagged(x)
            if eager:
                if expected_output is not None:
                    self.assertEqual(type(expected_output), type(output))
                    for ref_v, v in zip(
                        tree.flatten(expected_output), tree.flatten(output)
                    ):
                        self.assertAllClose(
                            ref_v,
                            v,
                            msg="Unexpected output value",
                            tpu_atol=tpu_atol,
                            tpu_rtol=tpu_rtol,
                        )
                if expected_num_losses is not None:
                    self.assertLen(layer.losses, expected_num_losses)

        def run_training_step(layer, input_data, output_data):
            class TestModel(Model):
                def __init__(self, layer):
                    super().__init__()
                    self.layer = layer

                def call(self, x, training=False):
                    return self.layer(x, training=training)

            model = TestModel(layer)

            data = (input_data, output_data)
            if backend.backend() == "torch":
                data = tree.map_structure(backend.convert_to_numpy, data)

            def data_generator():
                while True:
                    yield data

            # Single op loss to avoid compilation issues with ragged / sparse.
            class TestLoss(Loss):
                def __call__(self, y_true, y_pred, sample_weight=None):
                    return ops.sum(y_pred)

            # test the "default" path for each backend by setting
            # jit_compile="auto".
            # for tensorflow and jax backends auto is jitted
            # Note that tensorflow cannot be jitted with sparse tensors
            # for torch backend auto is eager
            #
            # NB: for torch, jit_compile=True turns on torchdynamo
            #  which may not always succeed in tracing depending
            #  on the model. Run your program with these env vars
            #  to get debug traces of dynamo:
            #    TORCH_LOGS="+dynamo"
            #    TORCHDYNAMO_VERBOSE=1
            #    TORCHDYNAMO_REPORT_GUARD_FAILURES=1
            jit_compile = "auto"
            if backend.backend() == "tensorflow" and input_sparse:
                jit_compile = False
            model.compile(
                optimizer="sgd", loss=TestLoss(), jit_compile=jit_compile
            )
            model.fit(data_generator(), steps_per_epoch=1, verbose=0)

        # Build test.
        if input_data is not None or input_shape is not None:
            if input_shape is None:
                build_shape = tree.map_structure(
                    lambda x: ops.shape(x), input_data
                )
            else:
                build_shape = input_shape
            layer = layer_cls(**init_kwargs)
            if isinstance(build_shape, dict):
                layer.build(**build_shape)
            else:
                layer.build(build_shape)
            run_build_asserts(layer)

            # Symbolic call test.
            if input_shape is None:
                keras_tensor_inputs = tree.map_structure(
                    lambda x: create_keras_tensors(
                        ops.shape(x), x.dtype, input_sparse, input_ragged
                    ),
                    input_data,
                )
            else:
                keras_tensor_inputs = create_keras_tensors(
                    input_shape, input_dtype, input_sparse, input_ragged
                )
            layer = layer_cls(**init_kwargs)
            if isinstance(keras_tensor_inputs, dict):
                keras_tensor_outputs = layer(
                    **keras_tensor_inputs, **call_kwargs
                )
            else:
                keras_tensor_outputs = layer(keras_tensor_inputs, **call_kwargs)
            run_build_asserts(layer)
            run_output_asserts(layer, keras_tensor_outputs, eager=False)

            if expected_mask_shape is not None:
                output_mask = layer.compute_mask(keras_tensor_inputs)
                self.assertEqual(expected_mask_shape, output_mask.shape)

            # The stateless layers should be built after instantiation.
            if assert_built_after_instantiation:
                layer = layer_cls(**init_kwargs)
                self.assertTrue(
                    layer.built,
                    msg=(
                        f"{type(layer)} is stateless, so it should be built "
                        "after instantiation."
                    ),
                )

                # Ensure that the subclass layer doesn't mark itself as built
                # when `build` is overridden.

                class ModifiedBuildLayer(layer_cls):
                    def build(self, *args, **kwargs):
                        pass

                layer = ModifiedBuildLayer(**init_kwargs)
                self.assertFalse(
                    layer.built,
                    msg=(
                        f"The `build` of {type(layer)} is overriden, so it "
                        "should not be built after instantiation."
                    ),
                )

        # Eager call test and compiled training test.
        if input_data is not None or input_shape is not None:
            if input_data is None:
                input_data = create_eager_tensors(
                    input_shape, input_dtype, input_sparse
                )
            layer = layer_cls(**init_kwargs)
            if isinstance(input_data, dict):
                output_data = layer(**input_data, **call_kwargs)
            else:
                output_data = layer(input_data, **call_kwargs)
            run_output_asserts(
                layer,
                output_data,
                eager=True,
                tpu_atol=tpu_atol,
                tpu_rtol=tpu_rtol,
            )

            if run_training_check and backend.backend() not in (
                "numpy",
                "openvino",
            ):
                run_training_step(layer, input_data, output_data)

            # Never test mixed precision on torch CPU. Torch lacks support.
            if run_mixed_precision_check and backend.backend() == "torch":
                import torch

                run_mixed_precision_check = torch.cuda.is_available()

            if run_mixed_precision_check:
                layer = layer_cls(**{**init_kwargs, "dtype": "mixed_float16"})
                input_spec = tree.map_structure(
                    lambda spec: KerasTensor(
                        spec.shape,
                        dtype=(
                            layer.compute_dtype
                            if layer.autocast
                            and backend.is_float_dtype(spec.dtype)
                            else spec.dtype
                        ),
                    ),
                    keras_tensor_inputs,
                )
                if isinstance(input_data, dict):
                    output_data = layer(**input_data, **call_kwargs)
                    output_spec = layer.compute_output_spec(**input_spec)
                else:
                    output_data = layer(input_data, **call_kwargs)
                    output_spec = layer.compute_output_spec(input_spec)
                for tensor, spec in zip(
                    tree.flatten(output_data), tree.flatten(output_spec)
                ):
                    dtype = standardize_dtype(tensor.dtype)
                    self.assertEqual(
                        dtype,
                        spec.dtype,
                        f"expected output dtype {spec.dtype}, got {dtype}",
                    )
                for weight in layer.weights:
                    dtype = standardize_dtype(weight.dtype)
                    if is_float_dtype(dtype):
                        self.assertEqual(dtype, "float32")