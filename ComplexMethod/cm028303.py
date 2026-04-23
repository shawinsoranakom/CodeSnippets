def create_target_assigner(reference, stage=None,
                           negative_class_weight=1.0, use_matmul_gather=False):
  """Factory function for creating standard target assigners.

  Args:
    reference: string referencing the type of TargetAssigner.
    stage: string denoting stage: {proposal, detection}.
    negative_class_weight: classification weight to be associated to negative
      anchors (default: 1.0)
    use_matmul_gather: whether to use matrix multiplication based gather which
      are better suited for TPUs.

  Returns:
    TargetAssigner: desired target assigner.

  Raises:
    ValueError: if combination reference+stage is invalid.
  """
  if reference == 'Multibox' and stage == 'proposal':
    if tf_version.is_tf2():
      raise ValueError('GreedyBipartiteMatcher is not supported in TF 2.X.')
    similarity_calc = sim_calc.NegSqDistSimilarity()
    matcher = bipartite_matcher.GreedyBipartiteMatcher()
    box_coder_instance = mean_stddev_box_coder.MeanStddevBoxCoder()

  elif reference == 'FasterRCNN' and stage == 'proposal':
    similarity_calc = sim_calc.IouSimilarity()
    matcher = argmax_matcher.ArgMaxMatcher(matched_threshold=0.7,
                                           unmatched_threshold=0.3,
                                           force_match_for_each_row=True,
                                           use_matmul_gather=use_matmul_gather)
    box_coder_instance = faster_rcnn_box_coder.FasterRcnnBoxCoder(
        scale_factors=[10.0, 10.0, 5.0, 5.0])

  elif reference == 'FasterRCNN' and stage == 'detection':
    similarity_calc = sim_calc.IouSimilarity()
    # Uses all proposals with IOU < 0.5 as candidate negatives.
    matcher = argmax_matcher.ArgMaxMatcher(matched_threshold=0.5,
                                           negatives_lower_than_unmatched=True,
                                           use_matmul_gather=use_matmul_gather)
    box_coder_instance = faster_rcnn_box_coder.FasterRcnnBoxCoder(
        scale_factors=[10.0, 10.0, 5.0, 5.0])

  elif reference == 'FastRCNN':
    similarity_calc = sim_calc.IouSimilarity()
    matcher = argmax_matcher.ArgMaxMatcher(matched_threshold=0.5,
                                           unmatched_threshold=0.1,
                                           force_match_for_each_row=False,
                                           negatives_lower_than_unmatched=False,
                                           use_matmul_gather=use_matmul_gather)
    box_coder_instance = faster_rcnn_box_coder.FasterRcnnBoxCoder()

  else:
    raise ValueError('No valid combination of reference and stage.')

  return TargetAssigner(similarity_calc, matcher, box_coder_instance,
                        negative_class_weight=negative_class_weight)