def _format_prediction_annotations(image_path, metadata, class_label_map=None, class_map=None) -> dict | None:
    """Format YOLO predictions for object detection visualization.

    Args:
        image_path (Path): Path to the image file.
        metadata (dict): Prediction metadata containing bounding boxes and class information.
        class_label_map (dict, optional): Mapping from class indices to class names.
        class_map (dict, optional): Additional class mapping for label conversion.

    Returns:
        (dict | None): Formatted prediction annotations or None if no predictions exist.
    """
    stem = image_path.stem
    image_id = int(stem) if stem.isnumeric() else stem

    predictions = metadata.get(image_id)
    if not predictions:
        LOGGER.debug(f"Comet Image: {image_path} has no bounding boxes predictions")
        return None

    # apply the mapping that was used to map the predicted classes when the JSON was created
    if class_label_map and class_map:
        class_label_map = {class_map[k]: v for k, v in class_label_map.items()}
    try:
        # import pycotools utilities to decompress annotations for various tasks, e.g. segmentation
        from faster_coco_eval.core.mask import decode
    except ImportError:
        decode = None

    data = []
    for prediction in predictions:
        boxes = prediction["bbox"]
        score = _scale_confidence_score(prediction["score"])
        cls_label = prediction["category_id"]
        if class_label_map:
            cls_label = str(class_label_map[cls_label])

        annotation_data = {"boxes": [boxes], "label": cls_label, "score": score}

        if decode is not None:
            # do segmentation processing only if we are able to decode it
            segments = prediction.get("segmentation", None)
            if segments is not None:
                segments = _extract_segmentation_annotation(segments, decode)
            if segments is not None:
                annotation_data["points"] = segments

        data.append(annotation_data)

    return {"name": "prediction", "data": data}