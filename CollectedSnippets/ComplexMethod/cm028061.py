def model_fn(features, mode, params):
    """The `model_fn` for TPUEstimator."""
    label_ids = None
    if mode != tf_estimator.ModeKeys.PREDICT:
      label_ids = features["label"]

    model_config = runner_config["model_config"]
    loss, logits = create_model(model, model_config, features, mode,
                                runner_config["name"])

    if mode == tf_estimator.ModeKeys.TRAIN:
      train_op = create_optimizer(loss, runner_config, params)
      return tf_estimator.tpu.TPUEstimatorSpec(
          mode=mode, loss=loss, train_op=train_op)
    elif mode == tf_estimator.ModeKeys.EVAL:
      if not runner_config["model_config"]["multilabel"]:
        metric_fn = metric_functions.classification_metric
      else:
        metric_fn = metric_functions.labeling_metric

      eval_metrics = (metric_fn, [loss, label_ids, logits])
      return tf_estimator.tpu.TPUEstimatorSpec(
          mode=mode, loss=loss, eval_metrics=eval_metrics)
    elif mode == tf_estimator.ModeKeys.PREDICT:
      predictions = {"logits": logits}
      if not runner_config["model_config"]["multilabel"]:
        predictions["predictions"] = tf.nn.softmax(logits)
      else:
        predictions["predictions"] = tf.math.sigmoid(logits)
      return tf_estimator.EstimatorSpec(mode=mode, predictions=predictions)
    else:
      assert False, "Expected to be called in TRAIN, EVAL, or PREDICT mode."