def test_Trainer_forward(batch_size,  # pylint:disable=too-many-locals
                         outputs,
                         _trainer_mocked,
                         mocker):
    """ Test that original trainer _forward calls the correct model methods """
    instance = _trainer_mocked(batch_size=batch_size)

    loss_returns = [torch.from_numpy(np.random.random((1, ))) for _ in range(outputs * 2)]
    mock_predictions = [torch.from_numpy(np.random.random((batch_size, 16, 16, 3)))
                        for _ in range(outputs * 2)]
    instance.model.model.return_value = mock_predictions
    instance.model.model.zero_grad = mocker.MagicMock()
    instance.model.model.loss = [mocker.MagicMock(return_value=ret) for ret in loss_returns]

    inputs = torch.from_numpy(np.random.random((2, batch_size, 16, 16, 3)))
    targets = [torch.from_numpy(np.random.random((2, batch_size, 16, 16, 3)))
               for _ in range(outputs)]

    # Call forwards
    result = instance._forward(inputs, targets)

    # Output comes from loss functions
    assert (np.allclose(e.numpy(), a.numpy()) for e, a in zip(result, loss_returns))

    # Model was zero'd
    instance.model.model.zero_grad.assert_called_once()

    # model forward pass called with inputs split
    train_call = instance.model.model

    call_args, call_kwargs = train_call.call_args
    assert call_kwargs == {"training": True}
    expected_inputs = [a.numpy() for a in inputs]
    actual_inputs = [a.numpy() for a in call_args[0]]
    assert (np.allclose(e, a) for e, a in zip(expected_inputs, actual_inputs))

    # losses called with targets split
    loss_calls = instance.model.model.loss
    expected_targets = [t[i].numpy() for i in range(2) for t in targets]
    expected_predictions = [p.numpy() for p in mock_predictions]
    for loss_call, pred, target in zip(loss_calls, expected_predictions, expected_targets):
        loss_call.assert_called_once()
        call_args, call_kwargs = loss_call.call_args
        assert not call_kwargs
        assert len(call_args) == 2

        actual_target = call_args[0].numpy()
        actual_pred = call_args[1].numpy()
        assert np.allclose(pred, actual_pred)
        assert np.allclose(target, actual_target)