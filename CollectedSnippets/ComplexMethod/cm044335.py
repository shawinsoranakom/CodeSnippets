def test_Trainer_forward(gpu_count, batch_size, outputs, _trainer_mocked, mocker):
    """ Test that original trainer _forward calls the correct model methods """
    instance, _ = _trainer_mocked(gpus=gpu_count, batch_size=batch_size)

    test_dims = (2, batch_size, 16, 16, 3)

    inputs = torch.from_numpy(np.random.random(test_dims)).to("cpu")
    targets = [torch.from_numpy(np.random.random(test_dims)).to("cpu")
               for _ in range(outputs)]

    loss_return = torch.rand((gpu_count * 2 * outputs), device="cpu")
    instance._distributed_model = mocker.MagicMock(return_value=loss_return)

    # Call the forward pass
    result = instance._forward(inputs, targets).cpu().numpy()

    # Make sure multi-outs are enabled
    if outputs > 1:
        assert instance._is_multi_out is True
    else:
        assert instance._is_multi_out is False

    # Make sure that our wrapped distributed model was called in the correct order
    instance._distributed_model.assert_called_once()
    call_args, call_kwargs = instance._distributed_model.call_args
    assert not call_kwargs
    assert len(call_args) == len(inputs) + (len(targets) * 2)

    expected_tgt = [t[i].cpu().numpy() for t in targets for i in range(2)]

    for expected, actual in zip([*inputs, *expected_tgt], call_args):
        assert np.allclose(expected, actual)

    # Make sure loss gets grouped, summed and scaled correctly
    expected = loss_return.cpu().numpy()
    expected = expected.reshape((gpu_count, 2, -1)).sum(axis=0).flatten() / gpu_count
    assert np.allclose(result, expected)