def main(_):
  assert FLAGS.train_image_dir, '`train_image_dir` missing.'
  assert FLAGS.val_image_dir, '`val_image_dir` missing.'
  assert FLAGS.test_image_dir, '`test_image_dir` missing.'
  assert FLAGS.train_annotations_file, '`train_annotations_file` missing.'
  assert FLAGS.val_annotations_file, '`val_annotations_file` missing.'
  assert FLAGS.testdev_annotations_file, '`testdev_annotations_file` missing.'

  if not tf.gfile.IsDirectory(FLAGS.output_dir):
    tf.gfile.MakeDirs(FLAGS.output_dir)
  train_output_path = os.path.join(FLAGS.output_dir, 'coco_train.record')
  val_output_path = os.path.join(FLAGS.output_dir, 'coco_val.record')
  testdev_output_path = os.path.join(FLAGS.output_dir, 'coco_testdev.record')

  _create_tf_record_from_coco_annotations(
      FLAGS.train_annotations_file,
      FLAGS.train_image_dir,
      train_output_path,
      FLAGS.include_masks,
      num_shards=100,
      keypoint_annotations_file=FLAGS.train_keypoint_annotations_file,
      densepose_annotations_file=FLAGS.train_densepose_annotations_file,
      remove_non_person_annotations=FLAGS.remove_non_person_annotations,
      remove_non_person_images=FLAGS.remove_non_person_images)
  _create_tf_record_from_coco_annotations(
      FLAGS.val_annotations_file,
      FLAGS.val_image_dir,
      val_output_path,
      FLAGS.include_masks,
      num_shards=50,
      keypoint_annotations_file=FLAGS.val_keypoint_annotations_file,
      densepose_annotations_file=FLAGS.val_densepose_annotations_file,
      remove_non_person_annotations=FLAGS.remove_non_person_annotations,
      remove_non_person_images=FLAGS.remove_non_person_images)
  _create_tf_record_from_coco_annotations(
      FLAGS.testdev_annotations_file,
      FLAGS.test_image_dir,
      testdev_output_path,
      FLAGS.include_masks,
      num_shards=50)