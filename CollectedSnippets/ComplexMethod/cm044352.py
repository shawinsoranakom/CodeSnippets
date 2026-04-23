def test_TorchTensorBoard_set_model(write_graph, _get_ttb_instance):
    """ Test that :class:`lib.training.tensorboard.set_model` functions """
    log_dir, instance = _get_ttb_instance(write_graph=write_graph)

    model = Sequential()
    model.add(layers.Input(shape=(8, )))
    model.add(layers.Dense(4))
    model.add(layers.Dense(4))

    assert not os.path.exists(os.path.join(log_dir, "train"))
    instance.set_model(model)
    instance.on_save()

    logs = [x for x in _get_logs(os.path.join(log_dir))
            if x.summary.value]

    if not write_graph:
        assert not logs
        return

    # Only a single logged entry
    assert len(logs) == 1 and len(logs[0].summary.value) == 1
    # Should be our Keras model summary
    assert logs[0].summary.value[0].tag == "keras/text_summary"