def tf_example_from_annotations_data_frame(annotations_data_frame, label_map,
                                           encoded_image):
  """Populates a TF Example message with image annotations from a data frame.

  Args:
    annotations_data_frame: Data frame containing the annotations for a single
      image.
    label_map: String to integer label map.
    encoded_image: The encoded image string

  Returns:
    The populated TF Example, if the label of at least one object is present in
    label_map. Otherwise, returns None.
  """

  filtered_data_frame = annotations_data_frame[
      annotations_data_frame.LabelName.isin(label_map)]
  filtered_data_frame_boxes = filtered_data_frame[
      ~filtered_data_frame.YMin.isnull()]
  filtered_data_frame_labels = filtered_data_frame[
      filtered_data_frame.YMin.isnull()]
  image_id = annotations_data_frame.ImageID.iloc[0]

  feature_map = {
      standard_fields.TfExampleFields.object_bbox_ymin:
          dataset_util.float_list_feature(
              filtered_data_frame_boxes.YMin.to_numpy()),
      standard_fields.TfExampleFields.object_bbox_xmin:
          dataset_util.float_list_feature(
              filtered_data_frame_boxes.XMin.to_numpy()),
      standard_fields.TfExampleFields.object_bbox_ymax:
          dataset_util.float_list_feature(
              filtered_data_frame_boxes.YMax.to_numpy()),
      standard_fields.TfExampleFields.object_bbox_xmax:
          dataset_util.float_list_feature(
              filtered_data_frame_boxes.XMax.to_numpy()),
      standard_fields.TfExampleFields.object_class_text:
          dataset_util.bytes_list_feature([
              six.ensure_binary(label_text)
              for label_text in filtered_data_frame_boxes.LabelName.to_numpy()
          ]),
      standard_fields.TfExampleFields.object_class_label:
          dataset_util.int64_list_feature(
              filtered_data_frame_boxes.LabelName.map(
                  lambda x: label_map[x]).to_numpy()),
      standard_fields.TfExampleFields.filename:
          dataset_util.bytes_feature(
              six.ensure_binary('{}.jpg'.format(image_id))),
      standard_fields.TfExampleFields.source_id:
          dataset_util.bytes_feature(six.ensure_binary(image_id)),
      standard_fields.TfExampleFields.image_encoded:
          dataset_util.bytes_feature(six.ensure_binary(encoded_image)),
  }

  if 'IsGroupOf' in filtered_data_frame.columns:
    feature_map[standard_fields.TfExampleFields.
                object_group_of] = dataset_util.int64_list_feature(
                    filtered_data_frame_boxes.IsGroupOf.to_numpy().astype(int))
  if 'IsOccluded' in filtered_data_frame.columns:
    feature_map[standard_fields.TfExampleFields.
                object_occluded] = dataset_util.int64_list_feature(
                    filtered_data_frame_boxes.IsOccluded.to_numpy().astype(
                        int))
  if 'IsTruncated' in filtered_data_frame.columns:
    feature_map[standard_fields.TfExampleFields.
                object_truncated] = dataset_util.int64_list_feature(
                    filtered_data_frame_boxes.IsTruncated.to_numpy().astype(
                        int))
  if 'IsDepiction' in filtered_data_frame.columns:
    feature_map[standard_fields.TfExampleFields.
                object_depiction] = dataset_util.int64_list_feature(
                    filtered_data_frame_boxes.IsDepiction.to_numpy().astype(
                        int))

  if 'ConfidenceImageLabel' in filtered_data_frame_labels.columns:
    feature_map[standard_fields.TfExampleFields.
                image_class_label] = dataset_util.int64_list_feature(
                    filtered_data_frame_labels.LabelName.map(
                        lambda x: label_map[x]).to_numpy())
    feature_map[standard_fields.TfExampleFields
                .image_class_text] = dataset_util.bytes_list_feature([
                    six.ensure_binary(label_text) for label_text in
                    filtered_data_frame_labels.LabelName.to_numpy()
                ]),
  return tf.train.Example(features=tf.train.Features(feature=feature_map))