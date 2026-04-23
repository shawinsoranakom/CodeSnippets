def _create_tf_record_from_coco_annotations(annotations_file, image_dir,
                                            output_path, include_masks,
                                            num_shards,
                                            keypoint_annotations_file='',
                                            densepose_annotations_file='',
                                            remove_non_person_annotations=False,
                                            remove_non_person_images=False):
  """Loads COCO annotation json files and converts to tf.Record format.

  Args:
    annotations_file: JSON file containing bounding box annotations.
    image_dir: Directory containing the image files.
    output_path: Path to output tf.Record file.
    include_masks: Whether to include instance segmentations masks
      (PNG encoded) in the result. default: False.
    num_shards: number of output file shards.
    keypoint_annotations_file: JSON file containing the person keypoint
      annotations. If empty, then no person keypoint annotations will be
      generated.
    densepose_annotations_file: JSON file containing the DensePose annotations.
      If empty, then no DensePose annotations will be generated.
    remove_non_person_annotations: Whether to remove any annotations that are
      not the "person" class.
    remove_non_person_images: Whether to remove any images that do not contain
      at least one "person" annotation.
  """
  with contextlib.ExitStack() as tf_record_close_stack, tf.gfile.GFile(
      annotations_file, 'r'
  ) as fid:
    output_tfrecords = tf_record_creation_util.open_sharded_output_tfrecords(
        tf_record_close_stack, output_path, num_shards)
    groundtruth_data = json.load(fid)
    images = groundtruth_data['images']
    category_index = label_map_util.create_category_index(
        groundtruth_data['categories'])

    annotations_index = {}
    if 'annotations' in groundtruth_data:
      logging.info('Found groundtruth annotations. Building annotations index.')
      for annotation in groundtruth_data['annotations']:
        image_id = annotation['image_id']
        if image_id not in annotations_index:
          annotations_index[image_id] = []
        annotations_index[image_id].append(annotation)
    missing_annotation_count = 0
    for image in images:
      image_id = image['id']
      if image_id not in annotations_index:
        missing_annotation_count += 1
        annotations_index[image_id] = []
    logging.info('%d images are missing annotations.',
                 missing_annotation_count)

    keypoint_annotations_index = {}
    if keypoint_annotations_file:
      with tf.gfile.GFile(keypoint_annotations_file, 'r') as kid:
        keypoint_groundtruth_data = json.load(kid)
      if 'annotations' in keypoint_groundtruth_data:
        for annotation in keypoint_groundtruth_data['annotations']:
          image_id = annotation['image_id']
          if image_id not in keypoint_annotations_index:
            keypoint_annotations_index[image_id] = {}
          keypoint_annotations_index[image_id][annotation['id']] = annotation

    densepose_annotations_index = {}
    if densepose_annotations_file:
      with tf.gfile.GFile(densepose_annotations_file, 'r') as fid:
        densepose_groundtruth_data = json.load(fid)
      if 'annotations' in densepose_groundtruth_data:
        for annotation in densepose_groundtruth_data['annotations']:
          image_id = annotation['image_id']
          if image_id not in densepose_annotations_index:
            densepose_annotations_index[image_id] = {}
          densepose_annotations_index[image_id][annotation['id']] = annotation

    total_num_annotations_skipped = 0
    total_num_keypoint_annotations_skipped = 0
    total_num_densepose_annotations_skipped = 0
    for idx, image in enumerate(images):
      if idx % 100 == 0:
        logging.info('On image %d of %d', idx, len(images))
      annotations_list = annotations_index[image['id']]
      keypoint_annotations_dict = None
      if keypoint_annotations_file:
        keypoint_annotations_dict = {}
        if image['id'] in keypoint_annotations_index:
          keypoint_annotations_dict = keypoint_annotations_index[image['id']]
      densepose_annotations_dict = None
      if densepose_annotations_file:
        densepose_annotations_dict = {}
        if image['id'] in densepose_annotations_index:
          densepose_annotations_dict = densepose_annotations_index[image['id']]
      (_, tf_example, num_annotations_skipped, num_keypoint_annotations_skipped,
       num_densepose_annotations_skipped) = create_tf_example(
           image, annotations_list, image_dir, category_index, include_masks,
           keypoint_annotations_dict, densepose_annotations_dict,
           remove_non_person_annotations, remove_non_person_images)
      total_num_annotations_skipped += num_annotations_skipped
      total_num_keypoint_annotations_skipped += num_keypoint_annotations_skipped
      total_num_densepose_annotations_skipped += (
          num_densepose_annotations_skipped)
      shard_idx = idx % num_shards
      if tf_example:
        output_tfrecords[shard_idx].write(tf_example.SerializeToString())
    logging.info('Finished writing, skipped %d annotations.',
                 total_num_annotations_skipped)
    if keypoint_annotations_file:
      logging.info('Finished writing, skipped %d keypoint annotations.',
                   total_num_keypoint_annotations_skipped)
    if densepose_annotations_file:
      logging.info('Finished writing, skipped %d DensePose annotations.',
                   total_num_densepose_annotations_skipped)