def evaluate(self):
    """Compute evaluation result.

    Returns:
      A named tuple with the following fields -
        average_precision: float numpy array of average precision for
            each class.
        mean_ap: mean average precision of all classes, float scalar
        precisions: List of precisions, each precision is a float numpy
            array
        recalls: List of recalls, each recall is a float numpy array
        corloc: numpy float array
        mean_corloc: Mean CorLoc score for each class, float scalar
    """
    if (self.num_gt_instances_per_class == 0).any():
      logging.warning(
          'The following classes have no ground truth examples: %s',
          np.squeeze(np.argwhere(self.num_gt_instances_per_class == 0)) +
          self.label_id_offset)

    if self.use_weighted_mean_ap:
      all_scores = np.array([], dtype=float)
      all_tp_fp_labels = np.array([], dtype=bool)
    for class_index in range(self.num_class):
      if self.num_gt_instances_per_class[class_index] == 0:
        continue
      if not self.scores_per_class[class_index]:
        scores = np.array([], dtype=float)
        tp_fp_labels = np.array([], dtype=float)
      else:
        scores = np.concatenate(self.scores_per_class[class_index])
        tp_fp_labels = np.concatenate(self.tp_fp_labels_per_class[class_index])
      if self.use_weighted_mean_ap:
        all_scores = np.append(all_scores, scores)
        all_tp_fp_labels = np.append(all_tp_fp_labels, tp_fp_labels)
      precision, recall = metrics.compute_precision_recall(
          scores, tp_fp_labels, self.num_gt_instances_per_class[class_index])
      recall_within_bound_indices = [
          index for index, value in enumerate(recall) if
          value >= self.recall_lower_bound and value <= self.recall_upper_bound
      ]
      recall_within_bound = recall[recall_within_bound_indices]
      precision_within_bound = precision[recall_within_bound_indices]

      self.precisions_per_class[class_index] = precision_within_bound
      self.recalls_per_class[class_index] = recall_within_bound
      self.sum_tp_class[class_index] = tp_fp_labels.sum()
      average_precision = metrics.compute_average_precision(
          precision_within_bound, recall_within_bound)
      self.average_precision_per_class[class_index] = average_precision
      logging.info(
          'class %d average_precision: %f', class_index, average_precision)

    self.corloc_per_class = metrics.compute_cor_loc(
        self.num_gt_imgs_per_class,
        self.num_images_correctly_detected_per_class)

    if self.use_weighted_mean_ap:
      num_gt_instances = np.sum(self.num_gt_instances_per_class)
      precision, recall = metrics.compute_precision_recall(
          all_scores, all_tp_fp_labels, num_gt_instances)
      recall_within_bound_indices = [
          index for index, value in enumerate(recall) if
          value >= self.recall_lower_bound and value <= self.recall_upper_bound
      ]
      recall_within_bound = recall[recall_within_bound_indices]
      precision_within_bound = precision[recall_within_bound_indices]
      mean_ap = metrics.compute_average_precision(precision_within_bound,
                                                  recall_within_bound)
    else:
      mean_ap = np.nanmean(self.average_precision_per_class)
    mean_corloc = np.nanmean(self.corloc_per_class)
    return ObjectDetectionEvalMetrics(self.average_precision_per_class, mean_ap,
                                      self.precisions_per_class,
                                      self.recalls_per_class,
                                      self.corloc_per_class, mean_corloc)