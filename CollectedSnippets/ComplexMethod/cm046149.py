def on_predict_postprocess_end(predictor: object, persist: bool = False) -> None:
    """Postprocess detected boxes and update with object tracking.

    Args:
        predictor (object): The predictor object containing the predictions.
        persist (bool, optional): Whether to persist the trackers if they already exist.

    Examples:
        Postprocess predictions and update with tracking
        >>> predictor = YourPredictorClass()
        >>> on_predict_postprocess_end(predictor, persist=True)
    """
    is_obb = predictor.args.task == "obb"
    is_stream = predictor.dataset.mode == "stream"
    for i, result in enumerate(predictor.results):
        tracker = predictor.trackers[i if is_stream else 0]
        vid_path = predictor.save_dir / Path(result.path).name
        if not persist and predictor.vid_path[i if is_stream else 0] != vid_path:
            tracker.reset()
            predictor.vid_path[i if is_stream else 0] = vid_path

        det = (result.obb if is_obb else result.boxes).cpu().numpy()
        tracks = tracker.update(det, result.orig_img, getattr(result, "feats", None))
        if len(tracks) == 0:
            continue
        idx = tracks[:, -1].astype(int)
        predictor.results[i] = result[idx]

        update_args = {"obb" if is_obb else "boxes": torch.as_tensor(tracks[:, :-1])}
        predictor.results[i].update(**update_args)