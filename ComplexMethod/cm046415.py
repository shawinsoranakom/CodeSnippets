def _log_plots(experiment, trainer) -> None:
    """Log evaluation plots and label plots for the experiment.

    This function logs various evaluation plots and confusion matrices to the experiment tracking system. It handles
    different types of metrics (SegmentMetrics, PoseMetrics, DetMetrics, OBBMetrics) and logs the appropriate plots for
    each type.

    Args:
        experiment (comet_ml.CometExperiment): The Comet ML experiment to log plots to.
        trainer (ultralytics.engine.trainer.BaseTrainer): The trainer object containing validation metrics and save
            directory information.

    Examples:
        >>> from ultralytics.utils.callbacks.comet import _log_plots
        >>> _log_plots(experiment, trainer)
    """
    plot_filenames = None
    if isinstance(trainer.validator.metrics, SegmentMetrics):
        plot_filenames = [
            trainer.save_dir / f"{prefix}{plots}.png"
            for plots in EVALUATION_PLOT_NAMES
            for prefix in SEGMENT_METRICS_PLOT_PREFIX
        ]
    elif isinstance(trainer.validator.metrics, PoseMetrics):
        plot_filenames = [
            trainer.save_dir / f"{prefix}{plots}.png"
            for plots in EVALUATION_PLOT_NAMES
            for prefix in POSE_METRICS_PLOT_PREFIX
        ]
    elif isinstance(trainer.validator.metrics, (DetMetrics, OBBMetrics)):
        plot_filenames = [
            trainer.save_dir / f"{prefix}{plots}.png"
            for plots in EVALUATION_PLOT_NAMES
            for prefix in DETECTION_METRICS_PLOT_PREFIX
        ]

    if plot_filenames is not None:
        _log_images(experiment, plot_filenames, None)

    confusion_matrix_filenames = [trainer.save_dir / f"{plots}.png" for plots in CONFUSION_MATRIX_PLOT_NAMES]
    _log_images(experiment, confusion_matrix_filenames, None)

    if not isinstance(trainer.validator.metrics, ClassifyMetrics):
        label_plot_filenames = [trainer.save_dir / f"{labels}.jpg" for labels in LABEL_PLOT_NAMES]
        _log_images(experiment, label_plot_filenames, None)