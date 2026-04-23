def test_task(trainer_cls, validator_cls, predictor_cls, data, model, weights):
    """Test YOLO training, validation, and prediction for various tasks."""
    overrides = {
        "data": data,
        "model": model,
        "imgsz": 32,
        "epochs": 1,
        "save": False,
        "mask_ratio": 1,
        "overlap_mask": False,
    }

    # Trainer
    trainer = trainer_cls(overrides=overrides)
    trainer.add_callback("on_train_start", test_func)
    assert test_func in trainer.callbacks["on_train_start"], "on_train_start callback not registered"
    trainer.train()

    # Validator
    cfg = get_cfg(DEFAULT_CFG)
    cfg.data = data
    cfg.imgsz = 32
    val = validator_cls(args=cfg)
    val.add_callback("on_val_start", test_func)
    assert test_func in val.callbacks["on_val_start"], "on_val_start callback not registered"
    val(model=trainer.best)

    # Predictor
    pred = predictor_cls(overrides={"imgsz": [64, 64]})
    pred.add_callback("on_predict_start", test_func)
    assert test_func in pred.callbacks["on_predict_start"], "on_predict_start callback not registered"

    # Determine model path for prediction
    model_path = weights if weights else trainer.best
    if model == "yolo26n.yaml":  # only for detection
        # Confirm there is no issue with sys.argv being empty
        with mock.patch.object(sys, "argv", []):
            result = pred(source=ASSETS, model=model_path)
            assert len(result) > 0, f"Predictor returned no results for {model}"
    else:
        result = pred(source=ASSETS, model=model_path)
        assert len(result) > 0, f"Predictor returned no results for {model}"

    # Test resume functionality
    with pytest.raises(AssertionError):
        trainer_cls(overrides={**overrides, "resume": trainer.last}).train()