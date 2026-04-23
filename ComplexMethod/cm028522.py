def find_similar_masks(
    results_1: DetectionResult,
    results_2: DetectionResult,
    num_detections: int,
    min_score_thresh: float,
    category_indices: List[List[Any]],
    category_index_combined: Dict[int, ItemDict],
    area_threshold: float,
    iou_threshold: float = 0.8,
) -> Dict[str, np.ndarray]:
  """Aligns the masks of the detections in `results_1` and `results_2`.

  Args:
    results_1: A dictionary which contains the results from the first model.
    results_2: A dictionary which contains the results from the second model.
    num_detections: The number of detections to consider.
    min_score_thresh: The minimum score threshold for a detection
    category_indices: list of sub lists which contains the labels of 1st and 2nd
      ML model
    category_index_combined: A dictionary with an object ID and nested
      dictionary with name. e.g. {1: {'id': 1, 'name': 'Fiber_Na_Bag',
      'supercategory': 'objects'}}
    area_threshold: Threshold for mask area consideration.
    iou_threshold: IOU threshold to compare masks.

  Returns:
     A dictionary containing the following keys:
       - num_detections: The number of aligned detections.
       - detection_classes: A NumPy array of shape (num_detections,) containing
       the classes for the aligned detections.
       - detection_scores: A NumPy array of shape (num_detections,) containing
       the scores for the aligned detections.
       - detection_boxes: A NumPy array of shape (num_detections, 4) containing
       the bounding boxes for the aligned detections.
       - detection_classes_names: A list of strings containing the names of the
       classes for the aligned detections.
       - detection_masks_reframed: A NumPy array of shape (num_detections,
       height, width) containing the full masks for the aligned detections.
  """
  detection_masks_reframed = []
  detection_scores = []
  detection_boxes = []
  detection_classes = []
  detection_classes_names = []

  aligned_masks = 0
  masks_list1 = results_1['detection_masks_reframed'][:num_detections]
  masks_list2 = results_2['detection_masks_reframed'][:num_detections]
  scores_list1 = results_1['detection_scores'][0]
  scores_list2 = results_2['detection_scores'][0]
  matched_masks_list2 = [False] * len(masks_list2)
  matched_masks_list1 = [False] * len(masks_list1)

  for i, mask1 in enumerate(masks_list1):
    if (scores_list1[i] > min_score_thresh) and (
        np.sum(mask1) < area_threshold
    ):
      is_similar = False

      for j, mask2 in enumerate(masks_list2):
        if scores_list2[j] > min_score_thresh and (
            np.sum(mask2) < area_threshold
        ):
          iou, union = calculate_iou(mask1, mask2)

          # masks which are present both in the 'detection_masks_reframed'
          # key of 'results_1' & 'results_2' dictionary
          if iou > iou_threshold:
            aligned_masks += 1
            is_similar = True
            matched_masks_list2[j] = True
            matched_masks_list1[i] = True

            detection_masks_reframed.append(union)

            avg_score, combined_box, combined_label, result_id = (
                calculate_combined_scores_boxes_classes(
                    i,
                    j,
                    results_1,
                    results_2,
                    category_indices,
                    category_index_combined,
                )
            )
            detection_scores.append(avg_score)
            detection_boxes.append(combined_box)
            detection_classes_names.append(combined_label)
            detection_classes.append(result_id)
            break

      # masks which are only present in the 'detection_masks_reframed'
      # of 'results_1' dictionary
      if not is_similar:
        aligned_masks += 1
        detection_masks_reframed.append(mask1)
        score, box, combined_label = calculate_single_result(
            i, results_1, category_indices[0], 'after'
        )
        detection_scores.append(score)
        detection_boxes.append(box)
        detection_classes_names.append(combined_label)
        result_id = find_id_by_name(category_index_combined, combined_label)
        detection_classes.append(result_id)

  # masks which are only present in the 'detection_masks_reframed'
  # key of 'results_2' dictionary
  for k, mask2 in enumerate(masks_list2):
    if (
        (not matched_masks_list2[k])
        and (scores_list2[k] > min_score_thresh)
        and (np.sum(mask2) < area_threshold)
    ):
      aligned_masks += 1
      detection_masks_reframed.append(mask2)
      score, box, combined_label = calculate_single_result(
          k, results_2, category_indices[1], 'before'
      )
      detection_scores.append(score)
      detection_boxes.append(box)
      detection_classes_names.append(combined_label)
      result_id = find_id_by_name(category_index_combined, combined_label)
      detection_classes.append(result_id)

  final_result = {
      'num_detections': np.array([aligned_masks]),
      'detection_classes': np.array(detection_classes),
      'detection_scores': np.array([detection_scores]),
      'detection_boxes': np.array([detection_boxes]),
      'detection_classes_names': np.array(detection_classes_names),
      'detection_masks_reframed': np.array(detection_masks_reframed),
  }

  return final_result