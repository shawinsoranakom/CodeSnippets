def on_predict_start(predictor: object, persist: bool = False) -> None:
    """Initialize trackers for object tracking during prediction.

    Args:
        predictor (ultralytics.engine.predictor.BasePredictor): The predictor object to initialize trackers for.
        persist (bool, optional): Whether to persist the trackers if they already exist.

    Examples:
        Initialize trackers for a predictor object
        >>> predictor = SomePredictorClass()
        >>> on_predict_start(predictor, persist=True)
    """
    if predictor.args.task == "classify":
        raise ValueError("❌ Classification doesn't support 'mode=track'")

    if hasattr(predictor, "trackers") and persist:
        return

    tracker = check_yaml(predictor.args.tracker)
    cfg = IterableSimpleNamespace(**YAML.load(tracker))

    if cfg.tracker_type not in {"bytetrack", "botsort"}:
        raise AssertionError(f"Only 'bytetrack' and 'botsort' are supported for now, but got '{cfg.tracker_type}'")

    predictor._feats = None  # reset in case used earlier
    if hasattr(predictor, "_hook"):
        predictor._hook.remove()
    if cfg.tracker_type == "botsort" and cfg.with_reid and cfg.model == "auto":
        from ultralytics.nn.modules.head import Detect

        if not (
            isinstance(predictor.model.model, torch.nn.Module)
            and isinstance(predictor.model.model.model[-1], Detect)
            and not predictor.model.model.model[-1].end2end
        ):
            cfg.model = "yolo26n-cls.pt"
        else:
            # Register hook to extract input of Detect layer
            def pre_hook(module, input):
                predictor._feats = list(input[0])  # unroll to new list to avoid mutation in forward

            predictor._hook = predictor.model.model.model[-1].register_forward_pre_hook(pre_hook)

    trackers = []
    for _ in range(predictor.dataset.bs):
        tracker = TRACKER_MAP[cfg.tracker_type](args=cfg, frame_rate=30)
        trackers.append(tracker)
        if predictor.dataset.mode != "stream":  # only need one tracker for other modes
            break
    predictor.trackers = trackers
    predictor.vid_path = [None] * predictor.dataset.bs