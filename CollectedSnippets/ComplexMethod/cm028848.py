def convert_predictions_to_coco_annotations(predictions):
  """Converts a batch of predictions to annotations in COCO format.

  Args:
    predictions: a dictionary of lists of numpy arrays including the following
      fields. 'K' below denotes the maximum number of instances per image.
      Required fields:
        - source_id: a list of numpy arrays of int or string of shape
            [batch_size].
        - detection_boxes: a list of numpy arrays of float of shape
            [batch_size, K, 4], where coordinates are in the original image
            space (not the scaled image space).
        - detection_classes: a list of numpy arrays of int of shape
            [batch_size, K].
        - detection_scores: a list of numpy arrays of float of shape
            [batch_size, K].
      Optional fields:
        - detection_masks: a list of numpy arrays of float of shape
            [batch_size, K, mask_height, mask_width].
        - detection_keypoints: a list of numpy arrays of float of shape
            [batch_size, K, num_keypoints, 2]

  Returns:
    coco_predictions: prediction in COCO annotation format.
  """
  coco_predictions = []
  num_batches = len(predictions['source_id'])
  max_num_detections = predictions['detection_classes'][0].shape[1]
  use_outer_box = 'detection_outer_boxes' in predictions
  for i in range(num_batches):
    predictions['detection_boxes'][i] = box_ops.yxyx_to_xywh(
        predictions['detection_boxes'][i])
    if use_outer_box:
      predictions['detection_outer_boxes'][i] = box_ops.yxyx_to_xywh(
          predictions['detection_outer_boxes'][i])
      mask_boxes = predictions['detection_outer_boxes']
    else:
      mask_boxes = predictions['detection_boxes']

    batch_size = predictions['source_id'][i].shape[0]
    if 'detection_keypoints' in predictions:
      # Adds extra ones to indicate the visibility for each keypoint as is
      # recommended by MSCOCO. Also, convert keypoint from [y, x] to [x, y]
      # as mandated by COCO.
      num_keypoints = predictions['detection_keypoints'][i].shape[2]
      coco_keypoints = np.concatenate(
          [
              predictions['detection_keypoints'][i][..., 1:],
              predictions['detection_keypoints'][i][..., :1],
              np.ones([batch_size, max_num_detections, num_keypoints, 1]),
          ],
          axis=-1,
      ).astype(int)
    for j in range(batch_size):
      if 'detection_masks' in predictions:
        image_masks = mask_ops.paste_instance_masks(
            predictions['detection_masks'][i][j],
            mask_boxes[i][j],
            int(predictions['image_info'][i][j, 0, 0]),
            int(predictions['image_info'][i][j, 0, 1]),
        )
        binary_masks = (image_masks > 0.0).astype(np.uint8)
        encoded_masks = [
            mask_api.encode(np.asfortranarray(binary_mask))
            for binary_mask in list(binary_masks)
        ]
      for k in range(max_num_detections):
        ann = {}
        ann['image_id'] = predictions['source_id'][i][j]
        ann['category_id'] = predictions['detection_classes'][i][j, k]
        ann['bbox'] = predictions['detection_boxes'][i][j, k]
        ann['score'] = predictions['detection_scores'][i][j, k]
        if 'detection_masks' in predictions:
          ann['segmentation'] = encoded_masks[k]
        if 'detection_keypoints' in predictions:
          ann['keypoints'] = coco_keypoints[j, k].flatten().tolist()
        coco_predictions.append(ann)

  for i, ann in enumerate(coco_predictions):
    ann['id'] = i + 1

  return coco_predictions