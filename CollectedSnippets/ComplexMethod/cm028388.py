def eval_coco_format(gt_json_file,
                     pred_json_file,
                     gt_folder=None,
                     pred_folder=None,
                     metric='pq',
                     num_categories=201,
                     ignored_label=0,
                     max_instances_per_category=256,
                     intersection_offset=None,
                     normalize_by_image_size=True,
                     num_workers=0,
                     print_digits=3):
  """Top-level code to compute metrics on a COCO-format result.

  Note that the default values are set for COCO panoptic segmentation dataset,
  and thus the users may want to change it for their own dataset evaluation.

  Args:
    gt_json_file: Path to a JSON file giving ground-truth annotations in COCO
      format.
    pred_json_file: Path to a JSON file for the predictions to evaluate.
    gt_folder: Folder containing panoptic-format ID images to match ground-truth
      annotations to image regions.
    pred_folder: Folder containing ID images for predictions.
    metric: Name of a metric to compute.
    num_categories: The number of segmentation categories (or "classes") in the
      dataset.
    ignored_label: A category id that is ignored in evaluation, e.g. the "void"
      label as defined in the COCO panoptic segmentation dataset.
    max_instances_per_category: The maximum number of instances for each
      category. Used in ensuring unique instance labels.
    intersection_offset: The maximum number of unique labels.
    normalize_by_image_size: Whether to normalize groundtruth instance region
      areas by image size. If True, groundtruth instance areas and weighted IoUs
      will be divided by the size of the corresponding image before accumulated
      across the dataset. Only used for Parsing Covering (pc) evaluation.
    num_workers: If set to a positive number, will spawn child processes to
      compute parts of the metric in parallel by splitting the images between
      the workers. If set to -1, will use the value of
      multiprocessing.cpu_count().
    print_digits: Number of significant digits to print in summary of computed
      metrics.

  Returns:
    The computed result of the metric as a float scalar.
  """
  with open(gt_json_file, 'r') as gt_json_fo:
    gt_json = json.load(gt_json_fo)
  with open(pred_json_file, 'r') as pred_json_fo:
    pred_json = json.load(pred_json_fo)
  if gt_folder is None:
    gt_folder = gt_json_file.replace('.json', '')
  if pred_folder is None:
    pred_folder = pred_json_file.replace('.json', '')
  if intersection_offset is None:
    intersection_offset = (num_categories + 1) * max_instances_per_category

  metric_aggregator = _build_metric(
      metric, num_categories, ignored_label, max_instances_per_category,
      intersection_offset, normalize_by_image_size)

  if num_workers == -1:
    logging.info('Attempting to get the CPU count to set # workers.')
    num_workers = multiprocessing.cpu_count()

  if num_workers > 0:
    logging.info('Computing metric in parallel with %d workers.', num_workers)
    work_queue = multiprocessing.Queue()
    result_queue = multiprocessing.Queue()
    workers = []
    worker_args = (metric_aggregator, gt_folder, pred_folder, work_queue,
                   result_queue)
    for _ in six.moves.range(num_workers):
      workers.append(
          multiprocessing.Process(target=_run_metrics_worker, args=worker_args))
    for worker in workers:
      worker.start()
    for ann_pair in _matched_annotations(gt_json, pred_json):
      work_queue.put(ann_pair, block=True)

    # Will cause each worker to return a result and terminate upon recieving a
    # None task.
    for _ in six.moves.range(num_workers):
      work_queue.put(None, block=True)

    # Retrieve results.
    for _ in six.moves.range(num_workers):
      metric_aggregator.merge(result_queue.get(block=True))

    for worker in workers:
      worker.join()
  else:
    logging.info('Computing metric in a single process.')
    annotation_pairs = _matched_annotations(gt_json, pred_json)
    _compute_metric(metric_aggregator, gt_folder, pred_folder, annotation_pairs)

  is_thing = _is_thing_array(gt_json['categories'], ignored_label)
  metric_aggregator.print_detailed_results(
      is_thing=is_thing, print_digits=print_digits)
  return metric_aggregator.detailed_results(is_thing=is_thing)