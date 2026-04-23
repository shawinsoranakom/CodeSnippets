def convert_label_map_to_categories(label_map,
                                    max_num_classes,
                                    use_display_name=True):
  """Given label map proto returns categories list compatible with eval.

  This function converts label map proto and returns a list of dicts, each of
  which  has the following keys:
    'id': (required) an integer id uniquely identifying this category.
    'name': (required) string representing category name
      e.g., 'cat', 'dog', 'pizza'.
    'keypoints': (optional) a dictionary of keypoint string 'label' to integer
      'id'.
  We only allow class into the list if its id-label_id_offset is
  between 0 (inclusive) and max_num_classes (exclusive).
  If there are several items mapping to the same id in the label map,
  we will only keep the first one in the categories list.

  Args:
    label_map: a StringIntLabelMapProto or None.  If None, a default categories
      list is created with max_num_classes categories.
    max_num_classes: maximum number of (consecutive) label indices to include.
    use_display_name: (boolean) choose whether to load 'display_name' field as
      category name.  If False or if the display_name field does not exist, uses
      'name' field as category names instead.

  Returns:
    categories: a list of dictionaries representing all possible categories.
  """
  categories = []
  list_of_ids_already_added = []
  if not label_map:
    label_id_offset = 1
    for class_id in range(max_num_classes):
      categories.append({
          'id': class_id + label_id_offset,
          'name': 'category_{}'.format(class_id + label_id_offset)
      })
    return categories
  for item in label_map.item:
    if not 0 < item.id <= max_num_classes:
      logging.info(
          'Ignore item %d since it falls outside of requested '
          'label range.', item.id)
      continue
    if use_display_name and item.HasField('display_name'):
      name = item.display_name
    else:
      name = item.name
    if item.id not in list_of_ids_already_added:
      list_of_ids_already_added.append(item.id)
      category = {'id': item.id, 'name': name}
      if item.HasField('frequency'):
        if item.frequency == string_int_label_map_pb2.LVISFrequency.Value(
            'FREQUENT'):
          category['frequency'] = 'f'
        elif item.frequency == string_int_label_map_pb2.LVISFrequency.Value(
            'COMMON'):
          category['frequency'] = 'c'
        elif item.frequency == string_int_label_map_pb2.LVISFrequency.Value(
            'RARE'):
          category['frequency'] = 'r'
      if item.HasField('instance_count'):
        category['instance_count'] = item.instance_count
      if item.keypoints:
        keypoints = {}
        list_of_keypoint_ids = []
        for kv in item.keypoints:
          if kv.id in list_of_keypoint_ids:
            raise ValueError('Duplicate keypoint ids are not allowed. '
                             'Found {} more than once'.format(kv.id))
          keypoints[kv.label] = kv.id
          list_of_keypoint_ids.append(kv.id)
        category['keypoints'] = keypoints
      categories.append(category)
  return categories