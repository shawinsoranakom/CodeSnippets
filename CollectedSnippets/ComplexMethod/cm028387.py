def compare_and_accumulate(
      self, groundtruth_category_array, groundtruth_instance_array,
      predicted_category_array, predicted_instance_array):
    """See base class."""
    # First, combine the category and instance labels so that every unique
    # value for (category, instance) is assigned a unique integer label.
    pred_segment_id = self._naively_combine_labels(predicted_category_array,
                                                   predicted_instance_array)
    gt_segment_id = self._naively_combine_labels(groundtruth_category_array,
                                                 groundtruth_instance_array)

    # Pre-calculate areas for all groundtruth and predicted segments.
    gt_segment_areas = _ids_to_counts(gt_segment_id)
    pred_segment_areas = _ids_to_counts(pred_segment_id)

    # We assume there is only one void segment and it has instance id = 0.
    void_segment_id = self.ignored_label * self.max_instances_per_category

    # There may be other ignored groundtruth segments with instance id > 0, find
    # those ids using the unique segment ids extracted with the area computation
    # above.
    ignored_segment_ids = {
        gt_segment_id for gt_segment_id in six.iterkeys(gt_segment_areas)
        if (gt_segment_id //
            self.max_instances_per_category) == self.ignored_label
    }

    # Next, combine the groundtruth and predicted labels. Dividing up the pixels
    # based on which groundtruth segment and which predicted segment they belong
    # to, this will assign a different 32-bit integer label to each choice
    # of (groundtruth segment, predicted segment), encoded as
    #   gt_segment_id * offset + pred_segment_id.
    intersection_id_array = (
        gt_segment_id.astype(np.uint32) * self.offset +
        pred_segment_id.astype(np.uint32))

    # For every combination of (groundtruth segment, predicted segment) with a
    # non-empty intersection, this counts the number of pixels in that
    # intersection.
    intersection_areas = _ids_to_counts(intersection_id_array)

    # Helper function that computes the area of the overlap between a predicted
    # segment and the ground-truth void/ignored segment.
    def prediction_void_overlap(pred_segment_id):
      void_intersection_id = void_segment_id * self.offset + pred_segment_id
      return intersection_areas.get(void_intersection_id, 0)

    # Compute overall ignored overlap.
    def prediction_ignored_overlap(pred_segment_id):
      total_ignored_overlap = 0
      for ignored_segment_id in ignored_segment_ids:
        intersection_id = ignored_segment_id * self.offset + pred_segment_id
        total_ignored_overlap += intersection_areas.get(intersection_id, 0)
      return total_ignored_overlap

    # Sets that are populated with which segments groundtruth/predicted segments
    # have been matched with overlapping predicted/groundtruth segments
    # respectively.
    gt_matched = set()
    pred_matched = set()

    # Calculate IoU per pair of intersecting segments of the same category.
    for intersection_id, intersection_area in six.iteritems(intersection_areas):
      gt_segment_id = intersection_id // self.offset
      pred_segment_id = intersection_id % self.offset

      gt_category = gt_segment_id // self.max_instances_per_category
      pred_category = pred_segment_id // self.max_instances_per_category
      if gt_category != pred_category:
        continue

      # Union between the groundtruth and predicted segments being compared does
      # not include the portion of the predicted segment that consists of
      # groundtruth "void" pixels.
      union = (
          gt_segment_areas[gt_segment_id] +
          pred_segment_areas[pred_segment_id] - intersection_area -
          prediction_void_overlap(pred_segment_id))
      iou = intersection_area / union
      if iou > 0.5:
        self.tp_per_class[gt_category] += 1
        self.iou_per_class[gt_category] += iou
        gt_matched.add(gt_segment_id)
        pred_matched.add(pred_segment_id)

    # Count false negatives for each category.
    for gt_segment_id in six.iterkeys(gt_segment_areas):
      if gt_segment_id in gt_matched:
        continue
      category = gt_segment_id // self.max_instances_per_category
      # Failing to detect a void segment is not a false negative.
      if category == self.ignored_label:
        continue
      self.fn_per_class[category] += 1

    # Count false positives for each category.
    for pred_segment_id in six.iterkeys(pred_segment_areas):
      if pred_segment_id in pred_matched:
        continue
      # A false positive is not penalized if is mostly ignored in the
      # groundtruth.
      if (prediction_ignored_overlap(pred_segment_id) /
          pred_segment_areas[pred_segment_id]) > 0.5:
        continue
      category = pred_segment_id // self.max_instances_per_category
      self.fp_per_class[category] += 1

    return self.result()