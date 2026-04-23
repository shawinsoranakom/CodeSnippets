def main(_):

  params = exp_factory.get_exp_config(_EXPERIMENT.value)
  for config_file in _CONFIG_FILE.value or []:
    params = hyperparams.override_params_dict(
        params, config_file, is_strict=True)
  if _PARAMS_OVERRIDE.value:
    params = hyperparams.override_params_dict(
        params, _PARAMS_OVERRIDE.value, is_strict=True)

  params.validate()
  params.lock()

  input_image_size = [int(x) for x in _INPUT_IMAGE_SIZE.value.split(',')]

  if isinstance(params.task,
                configs.image_classification.ImageClassificationTask):
    export_module_cls = export_module.ClassificationModule
  elif isinstance(params.task, configs.retinanet.RetinaNetTask):
    export_module_cls = export_module.DetectionModule
  elif isinstance(params.task,
                  configs.semantic_segmentation.SemanticSegmentationTask):
    export_module_cls = export_module.SegmentationModule
  else:
    raise TypeError(f'Export module for {type(params.task)} is not supported.')

  module = export_module_cls(
      params=params,
      batch_size=_BATCH_SIZE.value,
      input_image_size=input_image_size,
      input_type=_IMAGE_TYPE.value,
      num_channels=3)

  export_saved_model_lib.export_inference_graph(
      input_type=_IMAGE_TYPE.value,
      batch_size=_BATCH_SIZE.value,
      input_image_size=input_image_size,
      params=params,
      checkpoint_path=_CHECKPOINT_PATH.value,
      export_dir=_EXPORT_DIR.value,
      export_checkpoint_subdir=_EXPORT_CHECKPOINT_SUBDIR.value,
      export_saved_model_subdir=_EXPORT_SAVED_MODEL_SUBDIR.value,
      export_module=module,
      log_model_flops_and_params=_LOG_MODEL_FLOPS_AND_PARAMS.value,
      input_name=_INPUT_NAME.value)