def _maybe_update_config_with_key_value(configs, key, value):
  """Checks key type and updates `configs` with the key value pair accordingly.

  Args:
    configs: Dictionary of configuration objects. See outputs from
      get_configs_from_pipeline_file() or get_configs_from_multiple_files().
    key: String indicates the field(s) to be updated.
    value: Value used to override existing field value.

  Returns:
    A boolean value that indicates whether the override succeeds.

  Raises:
    ValueError: when the key string doesn't match any of the formats above.
  """
  is_valid_input_config_key, key_name, input_name, field_name = (
      check_and_parse_input_config_key(configs, key))
  if is_valid_input_config_key:
    update_input_reader_config(
        configs,
        key_name=key_name,
        input_name=input_name,
        field_name=field_name,
        value=value)
  elif field_name == "learning_rate":
    _update_initial_learning_rate(configs, value)
  elif field_name == "batch_size":
    _update_batch_size(configs, value)
  elif field_name == "momentum_optimizer_value":
    _update_momentum_optimizer_value(configs, value)
  elif field_name == "classification_localization_weight_ratio":
    # Localization weight is fixed to 1.0.
    _update_classification_localization_weight_ratio(configs, value)
  elif field_name == "focal_loss_gamma":
    _update_focal_loss_gamma(configs, value)
  elif field_name == "focal_loss_alpha":
    _update_focal_loss_alpha(configs, value)
  elif field_name == "train_steps":
    _update_train_steps(configs, value)
  elif field_name == "label_map_path":
    _update_label_map_path(configs, value)
  elif field_name == "mask_type":
    _update_mask_type(configs, value)
  elif field_name == "sample_1_of_n_eval_examples":
    _update_all_eval_input_configs(configs, "sample_1_of_n_examples", value)
  elif field_name == "eval_num_epochs":
    _update_all_eval_input_configs(configs, "num_epochs", value)
  elif field_name == "eval_with_moving_averages":
    _update_use_moving_averages(configs, value)
  elif field_name == "retain_original_images_in_eval":
    _update_retain_original_images(configs["eval_config"], value)
  elif field_name == "use_bfloat16":
    _update_use_bfloat16(configs, value)
  elif field_name == "retain_original_image_additional_channels_in_eval":
    _update_retain_original_image_additional_channels(configs["eval_config"],
                                                      value)
  elif field_name == "num_classes":
    _update_num_classes(configs["model"], value)
  elif field_name == "sample_from_datasets_weights":
    _update_sample_from_datasets_weights(configs["train_input_config"], value)
  elif field_name == "peak_max_pool_kernel_size":
    _update_peak_max_pool_kernel_size(configs["model"], value)
  elif field_name == "candidate_search_scale":
    _update_candidate_search_scale(configs["model"], value)
  elif field_name == "candidate_ranking_mode":
    _update_candidate_ranking_mode(configs["model"], value)
  elif field_name == "score_distance_offset":
    _update_score_distance_offset(configs["model"], value)
  elif field_name == "box_scale":
    _update_box_scale(configs["model"], value)
  elif field_name == "keypoint_candidate_score_threshold":
    _update_keypoint_candidate_score_threshold(configs["model"], value)
  elif field_name == "rescore_instances":
    _update_rescore_instances(configs["model"], value)
  elif field_name == "unmatched_keypoint_score":
    _update_unmatched_keypoint_score(configs["model"], value)
  elif field_name == "score_distance_multiplier":
    _update_score_distance_multiplier(configs["model"], value)
  elif field_name == "std_dev_multiplier":
    _update_std_dev_multiplier(configs["model"], value)
  elif field_name == "rescoring_threshold":
    _update_rescoring_threshold(configs["model"], value)
  else:
    return False
  return True