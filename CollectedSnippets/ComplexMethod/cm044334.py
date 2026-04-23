def test_WrappedModel(batch_size, outputs, mocker):
    """ Test that the wrapped model calls predictions and loss """
    model = mocker.MagicMock()
    instance = mod_distributed.WrappedModel(model)
    assert instance._keras_model is model

    loss_return = [torch.from_numpy((np.random.random((1, )))) for _ in range(outputs * 2)]
    model.loss = [mocker.MagicMock(return_value=ret) for ret in loss_return]

    test_dims = (batch_size, 16, 16, 3)

    inp_a = torch.from_numpy(np.random.random(test_dims))
    inp_b = torch.from_numpy(np.random.random(test_dims))
    targets = [torch.from_numpy(np.random.random(test_dims))
               for _ in range(outputs * 2)]
    predictions = [*torch.from_numpy(np.random.random((outputs * 2, *test_dims)))]

    model.return_value = predictions

    # Call forwards
    result = instance.forward(inp_a, inp_b, *targets)

    # Confirm model was called once forward with correct args
    model.assert_called_once()
    model_args, model_kwargs = model.call_args
    assert model_kwargs == {"training": True}
    assert len(model_args) == 1
    assert len(model_args[0]) == 2
    for real, expected in zip(model_args[0], [inp_a, inp_b]):
        assert np.allclose(real.numpy(), expected.numpy())

    # Confirm ZeroGrad called
    model.zero_grad.assert_called_once()

    # Confirm loss functions correctly called
    expected_targets = targets[0::2] + targets[1::2]

    for target, pred, loss in zip(expected_targets, predictions, model.loss):
        loss.assert_called_once()
        loss_args, loss_kwargs = loss.call_args
        assert not loss_kwargs
        assert len(loss_args) == 2
        for actual, expected in zip(loss_args, [target, pred]):
            assert np.allclose(actual.numpy(), expected.numpy())

    # Check that the result comes out as we put it in
    for expected, actual in zip(loss_return, result.squeeze()):
        assert np.isclose(expected.numpy(), actual.numpy())