def test_LearningRateFinder_on_batch_end(iteration,
                                         loss,
                                         learning_rate,
                                         best,
                                         stop_factor,
                                         beta,
                                         _trainer_mock,
                                         mocker):
    """ Test lib.train.LearingRateFinder._on_batch_end """
    trainer, model, optimizer = _trainer_mock()
    lrf = LearningRateFinder(trainer, stop_factor=stop_factor, beta=beta)
    optimizer.learning_rate.assign = mocker.MagicMock()
    optimizer.learning_rate.numpy = mocker.MagicMock(return_value=learning_rate)

    initial_avg = lrf._loss["avg"]
    lrf._loss["best"] = best
    lrf._on_batch_end(iteration, loss)

    assert lrf._metrics["learning_rates"][-1] == learning_rate
    assert lrf._loss["avg"] == (lrf._beta * initial_avg) + ((1 - lrf._beta) * loss)
    assert lrf._metrics["losses"][-1] == lrf._loss["avg"] / (1 - (lrf._beta ** iteration))

    if iteration > 1 and lrf._metrics["losses"][-1] > lrf._stop_factor * lrf._loss["best"]:
        assert model.model.stop_training is True
        optimizer.learning_rate.assign.assert_not_called()
        return

    if iteration == 1:
        assert lrf._loss["best"] == lrf._metrics["losses"][-1]

    assert model.model.stop_training is not True
    optimizer.learning_rate.assign.assert_called_with(
        learning_rate * lrf._lr_multiplier)