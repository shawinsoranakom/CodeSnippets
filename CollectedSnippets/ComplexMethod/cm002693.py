def is_valid_annotation_coco_panoptic(annotation: dict[str, list | tuple]) -> bool:
    if (
        isinstance(annotation, dict)
        and "image_id" in annotation
        and "segments_info" in annotation
        and "file_name" in annotation
        and isinstance(annotation["segments_info"], (list, tuple))
        and (
            # an image can have no segments
            len(annotation["segments_info"]) == 0 or isinstance(annotation["segments_info"][0], dict)
        )
    ):
        return True
    return False