def add_output_tensor_nodes(postprocessed_tensors,
                            output_collection_name='inference_op'):
  """Adds output nodes for detection boxes and scores.

  Adds the following nodes for output tensors -
    * num_detections: float32 tensor of shape [batch_size].
    * detection_boxes: float32 tensor of shape [batch_size, num_boxes, 4]
      containing detected boxes.
    * detection_scores: float32 tensor of shape [batch_size, num_boxes]
      containing scores for the detected boxes.
    * detection_multiclass_scores: (Optional) float32 tensor of shape
      [batch_size, num_boxes, num_classes_with_background] for containing class
      score distribution for detected boxes including background if any.
    * detection_features: (Optional) float32 tensor of shape
      [batch, num_boxes, roi_height, roi_width, depth]
      containing classifier features
      for each detected box
    * detection_classes: float32 tensor of shape [batch_size, num_boxes]
      containing class predictions for the detected boxes.
    * detection_keypoints: (Optional) float32 tensor of shape
      [batch_size, num_boxes, num_keypoints, 2] containing keypoints for each
      detection box.
    * detection_masks: (Optional) float32 tensor of shape
      [batch_size, num_boxes, mask_height, mask_width] containing masks for each
      detection box.

  Args:
    postprocessed_tensors: a dictionary containing the following fields
      'detection_boxes': [batch, max_detections, 4]
      'detection_scores': [batch, max_detections]
      'detection_multiclass_scores': [batch, max_detections,
        num_classes_with_background]
      'detection_features': [batch, num_boxes, roi_height, roi_width, depth]
      'detection_classes': [batch, max_detections]
      'detection_masks': [batch, max_detections, mask_height, mask_width]
        (optional).
      'detection_keypoints': [batch, max_detections, num_keypoints, 2]
        (optional).
      'num_detections': [batch]
    output_collection_name: Name of collection to add output tensors to.

  Returns:
    A tensor dict containing the added output tensor nodes.
  """
  detection_fields = fields.DetectionResultFields
  label_id_offset = 1
  boxes = postprocessed_tensors.get(detection_fields.detection_boxes)
  scores = postprocessed_tensors.get(detection_fields.detection_scores)
  multiclass_scores = postprocessed_tensors.get(
      detection_fields.detection_multiclass_scores)
  box_classifier_features = postprocessed_tensors.get(
      detection_fields.detection_features)
  raw_boxes = postprocessed_tensors.get(detection_fields.raw_detection_boxes)
  raw_scores = postprocessed_tensors.get(detection_fields.raw_detection_scores)
  classes = postprocessed_tensors.get(
      detection_fields.detection_classes) + label_id_offset
  keypoints = postprocessed_tensors.get(detection_fields.detection_keypoints)
  masks = postprocessed_tensors.get(detection_fields.detection_masks)
  num_detections = postprocessed_tensors.get(detection_fields.num_detections)
  outputs = {}
  outputs[detection_fields.detection_boxes] = tf.identity(
      boxes, name=detection_fields.detection_boxes)
  outputs[detection_fields.detection_scores] = tf.identity(
      scores, name=detection_fields.detection_scores)
  if multiclass_scores is not None:
    outputs[detection_fields.detection_multiclass_scores] = tf.identity(
        multiclass_scores, name=detection_fields.detection_multiclass_scores)
  if box_classifier_features is not None:
    outputs[detection_fields.detection_features] = tf.identity(
        box_classifier_features,
        name=detection_fields.detection_features)
  outputs[detection_fields.detection_classes] = tf.identity(
      classes, name=detection_fields.detection_classes)
  outputs[detection_fields.num_detections] = tf.identity(
      num_detections, name=detection_fields.num_detections)
  if raw_boxes is not None:
    outputs[detection_fields.raw_detection_boxes] = tf.identity(
        raw_boxes, name=detection_fields.raw_detection_boxes)
  if raw_scores is not None:
    outputs[detection_fields.raw_detection_scores] = tf.identity(
        raw_scores, name=detection_fields.raw_detection_scores)
  if keypoints is not None:
    outputs[detection_fields.detection_keypoints] = tf.identity(
        keypoints, name=detection_fields.detection_keypoints)
  if masks is not None:
    outputs[detection_fields.detection_masks] = tf.identity(
        masks, name=detection_fields.detection_masks)
  for output_key in outputs:
    tf.add_to_collection(output_collection_name, outputs[output_key])

  return outputs