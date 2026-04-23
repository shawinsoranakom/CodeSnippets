def compare_and_accumulate(self, groundtruths, predictions):
    """Compares predictions with ground-truths, and accumulates the metrics.

    It is not assumed that instance ids are unique across different categories.
    See for example combine_semantic_and_instance_predictions.py in official
    PanopticAPI evaluation code for issues to consider when fusing category
    and instance labels.

    Instances ids of the ignored category have the meaning that id 0 is "void"
    and remaining ones are crowd instances.

    Args:
      groundtruths: A dictionary contains ground-truth labels. It should contain
        the following fields.
        - category_mask: A 2D numpy uint16 array of ground-truth per-pixel
          category labels.
        - instance_mask: A 2D numpy uint16 array of ground-truth per-pixel
          instance labels.
      predictions: A dictionary contains the model outputs. It should contain
        the following fields.
        - category_array: A 2D numpy uint16 array of predicted per-pixel
          category labels.
        - instance_array: A 2D numpy uint16 array of predicted instance labels.
    """
    groundtruth_category_mask = groundtruths['category_mask']
    groundtruth_instance_mask = groundtruths['instance_mask']
    predicted_category_mask = predictions['category_mask']
    predicted_instance_mask = predictions['instance_mask']

    # First, combine the category and instance labels so that every unique
    # value for (category, instance) is assigned a unique integer label.
    pred_segment_id = self._naively_combine_labels(predicted_category_mask,
                                                   predicted_instance_mask)
    gt_segment_id = self._naively_combine_labels(groundtruth_category_mask,
                                                 groundtruth_instance_mask)

    # Pre-calculate areas for all ground-truth and predicted segments.
    gt_segment_areas = _ids_to_counts(gt_segment_id)
    pred_segment_areas = _ids_to_counts(pred_segment_id)

    # We assume there is only one void segment and it has instance id = 0.
    void_segment_id = self.ignored_label * self.max_instances_per_category

    # There may be other ignored ground-truth segments with instance id > 0,
    # find those ids using the unique segment ids extracted with the area
    # computation above.
    ignored_segment_ids = {
        gt_segment_id for gt_segment_id in gt_segment_areas
        if (gt_segment_id //
            self.max_instances_per_category) == self.ignored_label
    }

    # Next, combine the ground-truth and predicted labels. Divide up the pixels
    # based on which ground-truth segment and predicted segment they belong to,
    # this will assign a different 32-bit integer label to each choice of
    # (ground-truth segment, predicted segment), encoded as
    #   gt_segment_id * offset + pred_segment_id.
    intersection_id_array = (
        gt_segment_id.astype(np.uint64) * self.offset +
        pred_segment_id.astype(np.uint64))

    # For every combination of (ground-truth segment, predicted segment) with a
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

    # Sets that are populated with segments which ground-truth/predicted
    # segments have been matched with overlapping predicted/ground-truth
    # segments respectively.
    gt_matched = set()
    pred_matched = set()

    # Calculate IoU per pair of intersecting segments of the same category.
    for intersection_id, intersection_area in intersection_areas.items():
      gt_segment_id = int(intersection_id // self.offset)
      pred_segment_id = int(intersection_id % self.offset)

      gt_category = int(gt_segment_id // self.max_instances_per_category)
      pred_category = int(pred_segment_id // self.max_instances_per_category)
      if gt_category != pred_category:
        continue

      # Union between the ground-truth and predicted segments being compared
      # does not include the portion of the predicted segment that consists of
      # ground-truth "void" pixels.
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
    for gt_segment_id in gt_segment_areas:
      if gt_segment_id in gt_matched:
        continue
      category = gt_segment_id // self.max_instances_per_category
      # Failing to detect a void segment is not a false negative.
      if category == self.ignored_label:
        continue
      self.fn_per_class[category] += 1

    # Count false positives for each category.
    for pred_segment_id in pred_segment_areas:
      if pred_segment_id in pred_matched:
        continue
      # A false positive is not penalized if is mostly ignored in the
      # ground-truth.
      if (prediction_ignored_overlap(pred_segment_id) /
          pred_segment_areas[pred_segment_id]) > 0.5:
        continue
      category = pred_segment_id // self.max_instances_per_category
      self.fp_per_class[category] += 1