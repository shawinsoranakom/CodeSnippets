def filter_detections(
    results: Mapping[str, np.ndarray],
    valid_indices: Sequence[int] | Sequence[bool],
) -> Mapping[str, np.ndarray]:
  """Filter the detection results based on the valid indices.

  Args:
    results: The detection results from the model.
    valid_indices: The indices of the valid detections.

  Returns:
    The filtered detection results.
  """
  if np.array(valid_indices).dtype == bool:
    new_num_detections = int(np.sum(valid_indices))
  else:
    new_num_detections = len(valid_indices)

  # Define the keys to filter
  keys_to_filter = [
      'detection_masks',
      'detection_masks_resized',
      'detection_masks_reframed',
      'detection_classes',
      'detection_boxes',
      'normalized_boxes',
      'detection_scores',
  ]

  filtered_output = {}

  for key in keys_to_filter:
    if key in results:
      if key == 'detection_masks':
        filtered_output[key] = results[key][:, valid_indices, :, :]
      elif key in ['detection_masks_resized', 'detection_masks_reframed']:
        filtered_output[key] = results[key][valid_indices, :, :]
      elif key in ['detection_boxes', 'normalized_boxes']:
        filtered_output[key] = results[key][:, valid_indices, :]
      elif key in [
          'detection_classes',
          'detection_scores',
          'detection_classes_names',
      ]:
        filtered_output[key] = results[key][:, valid_indices]
  filtered_output['image_info'] = results['image_info']
  filtered_output['num_detections'] = np.array([new_num_detections])

  return filtered_output