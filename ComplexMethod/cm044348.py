def test_LearningRateFinder_train(iters,  # pylint:disable=too-many-locals
                                  mode,
                                  strength,
                                  _trainer_mock,
                                  mocker):
    """ Test lib.train.LearingRateFinder._train """
    trainer, _, _ = _trainer_mock(iters, mode, strength)

    mock_loss_return = np.random.rand(2).tolist()
    trainer.train_one_batch = mocker.MagicMock(return_value=mock_loss_return)

    lrf = LearningRateFinder(trainer)

    lrf._on_batch_end = mocker.MagicMock()
    lrf._update_description = mocker.MagicMock()

    lrf._train()

    trainer.train_one_batch.assert_called()
    assert trainer.train_one_batch.call_count == iters

    train_call_args = [mocker.call(x + 1, mock_loss_return[0]) for x in range(iters)]
    assert lrf._on_batch_end.call_args_list == train_call_args

    lrf._update_description.assert_called()
    assert lrf._update_description.call_count == iters

    # NaN break
    mock_loss_return = (np.nan, np.nan)
    trainer.train_one_batch = mocker.MagicMock(return_value=mock_loss_return)

    lrf._train()

    assert trainer.train_one_batch.call_count == 1  # Called once

    assert lrf._update_description.call_count == iters  # Not called
    assert lrf._on_batch_end.call_count == iters