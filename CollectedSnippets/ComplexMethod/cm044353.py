def test_TorchTensorBoard_on_train_batch_end(batch, logs, _get_ttb_instance):
    """ Test that :class:`lib.training.tensorboard.on_train_batch_end` functions """
    log_dir, instance = _get_ttb_instance()

    assert not os.path.exists(os.path.join(log_dir, "train"))

    instance.on_train_batch_end(batch, logs)
    instance.on_save()

    tb_logs = [x for x in _get_logs(os.path.join(log_dir))
               if x.summary.value]

    assert len(tb_logs) == len(logs)
    for (k, v), out in zip(logs.items(), tb_logs):
        assert len(out.summary.value) == 1
        assert out.summary.value[0].tag == f"batch_{k}"
        assert np.isclose(out.summary.value[0].simple_value, v)
        assert out.step == batch