def ssd_random_crop_pad_fixed_aspect_ratio(
    image,
    boxes,
    labels,
    label_weights,
    label_confidences=None,
    multiclass_scores=None,
    masks=None,
    keypoints=None,
    min_object_covered=(0.0, 0.1, 0.3, 0.5, 0.7, 0.9, 1.0),
    aspect_ratio=1.0,
    aspect_ratio_range=((0.5, 2.0),) * 7,
    area_range=((0.1, 1.0),) * 7,
    overlap_thresh=(0.0, 0.1, 0.3, 0.5, 0.7, 0.9, 1.0),
    clip_boxes=(True,) * 7,
    random_coef=(0.15,) * 7,
    min_padded_size_ratio=(1.0, 1.0),
    max_padded_size_ratio=(2.0, 2.0),
    seed=None,
    preprocess_vars_cache=None):
  """Random crop and pad preprocessing with default parameters as in SSD paper.

  Liu et al., SSD: Single shot multibox detector.
  For further information on random crop preprocessing refer to RandomCrop
  function above.

  The only difference is that after the initial crop, images are zero-padded
  to a fixed aspect ratio instead of being resized to that aspect ratio.

  Args:
    image: rank 3 float32 tensor contains 1 image -> [height, width, channels]
           with pixel values varying between [0, 1].
    boxes: rank 2 float32 tensor containing the bounding boxes -> [N, 4].
           Boxes are in normalized form meaning their coordinates vary
           between [0, 1].
           Each row is in the form of [ymin, xmin, ymax, xmax].
    labels: rank 1 int32 tensor containing the object classes.
    label_weights: float32 tensor of shape [num_instances] representing the
      weight for each box.
    label_confidences: (optional) float32 tensor of shape [num_instances]
      representing the confidence for each box.
    multiclass_scores: (optional) float32 tensor of shape
      [num_instances, num_classes] representing the score for each box for each
      class.
    masks: (optional) rank 3 float32 tensor with shape
           [num_instances, height, width] containing instance masks. The masks
           are of the same height, width as the input `image`.
    keypoints: (optional) rank 3 float32 tensor with shape
               [num_instances, num_keypoints, 2]. The keypoints are in y-x
               normalized coordinates.
    min_object_covered: the cropped image must cover at least this fraction of
                        at least one of the input bounding boxes.
    aspect_ratio: the final aspect ratio to pad to.
    aspect_ratio_range: allowed range for aspect ratio of cropped image.
    area_range: allowed range for area ratio between cropped image and the
                original image.
    overlap_thresh: minimum overlap thresh with new cropped
                    image to keep the box.
    clip_boxes: whether to clip the boxes to the cropped image.
    random_coef: a random coefficient that defines the chance of getting the
                 original image. If random_coef is 0, we will always get the
                 cropped image, and if it is 1.0, we will always get the
                 original image.
    min_padded_size_ratio: min ratio of padded image height and width to the
                           input image's height and width.
    max_padded_size_ratio: max ratio of padded image height and width to the
                           input image's height and width.
    seed: random seed.
    preprocess_vars_cache: PreprocessorCache object that records previously
                           performed augmentations. Updated in-place. If this
                           function is called multiple times with the same
                           non-null cache, it will perform deterministically.

  Returns:
    image: image which is the same rank as input image.
    boxes: boxes which is the same rank as input boxes.
           Boxes are in normalized form.
    labels: new labels.

    If multiclass_scores, masks, or keypoints is not None, the function also
    returns:

    multiclass_scores: rank 2 with shape [num_instances, num_classes]
    masks: rank 3 float32 tensor with shape [num_instances, height, width]
           containing instance masks.
    keypoints: rank 3 float32 tensor with shape
               [num_instances, num_keypoints, 2]
  """
  crop_result = ssd_random_crop(
      image,
      boxes,
      labels,
      label_weights=label_weights,
      label_confidences=label_confidences,
      multiclass_scores=multiclass_scores,
      masks=masks,
      keypoints=keypoints,
      min_object_covered=min_object_covered,
      aspect_ratio_range=aspect_ratio_range,
      area_range=area_range,
      overlap_thresh=overlap_thresh,
      clip_boxes=clip_boxes,
      random_coef=random_coef,
      seed=seed,
      preprocess_vars_cache=preprocess_vars_cache)
  i = 3
  new_image, new_boxes, new_labels = crop_result[:i]
  new_label_weights = None
  new_label_confidences = None
  new_multiclass_scores = None
  new_masks = None
  new_keypoints = None
  if label_weights is not None:
    new_label_weights = crop_result[i]
    i += 1
  if label_confidences is not None:
    new_label_confidences = crop_result[i]
    i += 1
  if multiclass_scores is not None:
    new_multiclass_scores = crop_result[i]
    i += 1
  if masks is not None:
    new_masks = crop_result[i]
    i += 1
  if keypoints is not None:
    new_keypoints = crop_result[i]

  result = random_pad_to_aspect_ratio(
      new_image,
      new_boxes,
      masks=new_masks,
      keypoints=new_keypoints,
      aspect_ratio=aspect_ratio,
      min_padded_size_ratio=min_padded_size_ratio,
      max_padded_size_ratio=max_padded_size_ratio,
      seed=seed,
      preprocess_vars_cache=preprocess_vars_cache)

  result = list(result)
  i = 3
  result.insert(2, new_labels)
  if new_label_weights is not None:
    result.insert(i, new_label_weights)
    i += 1
  if new_label_confidences is not None:
    result.insert(i, new_label_confidences)
    i += 1
  if multiclass_scores is not None:
    result.insert(i, new_multiclass_scores)
  result = tuple(result)

  return result