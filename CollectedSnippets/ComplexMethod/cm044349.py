def test_init(model_fixture: Model, target_lr: float, steps: int) -> None:
    """ Test class initializes correctly """
    instance = LearningRateWarmup(model_fixture, target_lr, steps)

    attrs = ["_model", "_target_lr", "_steps", "_current_lr", "_current_step", "_reporting_points"]
    assert all(a in instance.__dict__ for a in attrs)
    assert all(a in attrs for a in instance.__dict__)
    assert instance._current_lr == 0.0
    assert instance._current_step == 0

    assert isinstance(instance._model, Model)
    assert instance._target_lr == target_lr
    assert instance._steps == steps

    assert len(instance._reporting_points) == 11
    assert all(isinstance(x, int) for x in instance._reporting_points)
    assert instance._reporting_points == [int(steps * i / 10) for i in range(11)]