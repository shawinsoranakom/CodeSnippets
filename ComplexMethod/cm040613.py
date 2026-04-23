def _test_layer(
        self,
        model_name,
        layer_class,
        layer_init_kwargs,
        trainable_weights,
        trainable_params,
        non_trainable_weights,
        non_trainable_params,
    ):
        layer_init_kwargs.update(self.init_kwargs)

        # Fake MNIST data
        x_train = random.uniform(shape=(320, 28, 28, 1))
        y_train_indices = ops.cast(
            ops.random.uniform(shape=(320,), minval=0, maxval=num_classes),
            dtype="int32",
        )
        y_train = ops.one_hot(y_train_indices, num_classes, dtype="int32")
        x_test = random.uniform(shape=(32, 28, 28, 1))

        def _count_params(weights):
            count = 0
            for weight in weights:
                count = count + math.prod(ops.shape(weight))
            return count

        def verify_weights_and_params(layer):
            self.assertEqual(trainable_weights, len(layer.trainable_weights))
            self.assertEqual(
                trainable_params,
                _count_params(layer.trainable_weights),
            )
            self.assertEqual(
                non_trainable_weights, len(layer.non_trainable_weights)
            )
            self.assertEqual(
                non_trainable_params,
                _count_params(layer.non_trainable_weights),
            )

        # functional model
        layer1 = layer_class(**layer_init_kwargs)
        inputs1 = layers.Input(shape=input_shape)
        outputs1 = layer1(inputs1)
        model1 = models.Model(
            inputs=inputs1, outputs=outputs1, name=f"{model_name}1"
        )
        model1.summary()

        verify_weights_and_params(layer1)

        model1.compile(
            loss="categorical_crossentropy",
            optimizer="adam",
            metrics=[metrics.CategoricalAccuracy()],
        )

        tw1_before_fit = tree.map_structure(
            backend.convert_to_numpy, layer1.trainable_weights
        )
        ntw1_before_fit = tree.map_structure(
            backend.convert_to_numpy, layer1.non_trainable_weights
        )
        model1.fit(x_train, y_train, epochs=1, steps_per_epoch=10)
        tw1_after_fit = tree.map_structure(
            backend.convert_to_numpy, layer1.trainable_weights
        )
        ntw1_after_fit = tree.map_structure(
            backend.convert_to_numpy, layer1.non_trainable_weights
        )

        # verify both trainable and non-trainable weights did change after fit
        for before, after in zip(tw1_before_fit, tw1_after_fit):
            self.assertNotAllClose(before, after)
        for before, after in zip(ntw1_before_fit, ntw1_after_fit):
            self.assertNotAllClose(before, after)

        expected_output_shape = (ops.shape(x_test)[0], num_classes)
        output1 = model1(x_test)
        self.assertEqual(output1.shape, expected_output_shape)
        predict1 = model1.predict(x_test, steps=1)
        self.assertEqual(predict1.shape, expected_output_shape)

        # verify both trainable and non-trainable weights did not change
        tw1_after_call = tree.map_structure(
            backend.convert_to_numpy, layer1.trainable_weights
        )
        ntw1_after_call = tree.map_structure(
            backend.convert_to_numpy, layer1.non_trainable_weights
        )
        for after_fit, after_call in zip(tw1_after_fit, tw1_after_call):
            self.assertAllClose(after_fit, after_call)
        for after_fit, after_call in zip(ntw1_after_fit, ntw1_after_call):
            self.assertAllClose(after_fit, after_call)

        exported_params = jax.tree_util.tree_map(
            backend.convert_to_numpy, layer1.params
        )
        if layer1.state is not None:
            exported_state = jax.tree_util.tree_map(
                backend.convert_to_numpy, layer1.state
            )
        else:
            exported_state = None

        def verify_identical_model(model):
            output = model(x_test)
            self.assertAllClose(output1, output)

            predict = model.predict(x_test, steps=1)
            self.assertAllClose(predict1, predict)

        # sequential model to compare results
        layer2 = layer_class(
            params=exported_params,
            state=exported_state,
            input_shape=input_shape,
            **layer_init_kwargs,
        )
        model2 = models.Sequential([layer2], name=f"{model_name}2")
        model2.summary()
        verify_weights_and_params(layer2)
        model2.compile(
            loss="categorical_crossentropy",
            optimizer="adam",
            metrics=[metrics.CategoricalAccuracy()],
        )
        verify_identical_model(model2)

        # save, load back and compare results
        path = os.path.join(self.get_temp_dir(), "jax_layer_model.keras")
        model2.save(path)

        model3 = saving.load_model(path)
        layer3 = model3.layers[0]
        model3.summary()
        verify_weights_and_params(layer3)
        verify_identical_model(model3)

        # export, load back and compare results
        path = os.path.join(self.get_temp_dir(), "jax_layer_export")
        export_kwargs = {}
        if testing.jax_uses_gpu():
            export_kwargs = {
                "jax2tf_kwargs": {
                    "native_serialization_platforms": ("cpu", "cuda")
                }
            }
        elif testing.jax_uses_tpu():
            export_kwargs = {
                "jax2tf_kwargs": {
                    "native_serialization_platforms": ("cpu", "tpu")
                }
            }
        model2.export(path, format="tf_saved_model", **export_kwargs)
        model4 = tf.saved_model.load(path)
        output4 = model4.serve(x_test)
        self.assertAllClose(output1, output4, atol=1e-2, rtol=1e-3)

        # test subclass model building without a build method
        class TestModel(models.Model):
            def __init__(self, layer):
                super().__init__()
                self._layer = layer

            def call(self, inputs):
                return self._layer(inputs)

        layer5 = layer_class(**layer_init_kwargs)
        model5 = TestModel(layer5)
        output5 = model5(x_test)
        self.assertNotAllClose(output5, 0.0)