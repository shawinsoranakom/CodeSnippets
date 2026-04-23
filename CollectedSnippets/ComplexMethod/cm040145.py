def get_model(type="sequential", input_shape=(10,), layer_list=None):
    layer_list = layer_list or [
        layers.Dense(10, activation="relu"),
        layers.BatchNormalization(),
        layers.Dense(1, activation="sigmoid"),
    ]
    if type == "sequential":
        model = models.Sequential(layer_list)
        model.build(input_shape=(None,) + input_shape)
        return model
    if type == "functional":
        input = output = tree.map_shape_structure(layers.Input, input_shape)
        for layer in layer_list:
            output = layer(output)
        return models.Model(inputs=input, outputs=output)
    if type == "subclass":
        model = CustomModel(layer_list)
        model.build(input_shape=(None,) + input_shape)
        # Trace the model with dummy data to ensure it's properly built for
        # export
        dummy_input = np.zeros((1,) + input_shape, dtype=np.float32)
        _ = model(dummy_input)  # This traces the model
        return model
    if type == "lstm":
        inputs = layers.Input((4, 10))
        x = layers.Bidirectional(
            layers.LSTM(
                10,
                kernel_initializer="he_normal",
                return_sequences=True,
                kernel_regularizer=None,
            ),
            merge_mode="sum",
        )(inputs)
        outputs = layers.Bidirectional(
            layers.LSTM(
                10,
                kernel_initializer="he_normal",
                return_sequences=True,
                kernel_regularizer=None,
            ),
            merge_mode="concat",
        )(x)
        return models.Model(inputs=inputs, outputs=outputs)
    if type == "multi_input":
        input1 = layers.Input(shape=input_shape, name="input1")
        input2 = layers.Input(shape=input_shape, name="input2")
        x1 = layers.Dense(10, activation="relu")(input1)
        x2 = layers.Dense(10, activation="relu")(input2)
        combined = layers.concatenate([x1, x2])
        output = layers.Dense(1, activation="sigmoid")(combined)
        return models.Model(inputs=[input1, input2], outputs=output)
    if type == "multi_output":
        inputs = layers.Input(shape=input_shape)
        shared = layers.Dense(20, activation="relu")(inputs)
        output1 = layers.Dense(1, activation="sigmoid", name="output1")(shared)
        output2 = layers.Dense(3, activation="softmax", name="output2")(shared)
        return models.Model(inputs=inputs, outputs=[output1, output2])
    raise ValueError(f"Unknown model type: {type}")