def get_label_map_dict(label_map_path_or_proto,
                       use_display_name=False,
                       fill_in_gaps_and_background=False,
                       validator=None):
  """Reads a label map and returns a dictionary of label names to id.

  Args:
    label_map_path_or_proto: path to StringIntLabelMap proto text file or the
      proto itself.
    use_display_name: whether to use the label map items' display names as keys.
    fill_in_gaps_and_background: whether to fill in gaps and background with
    respect to the id field in the proto. The id: 0 is reserved for the
    'background' class and will be added if it is missing. All other missing
    ids in range(1, max(id)) will be added with a dummy class name
    ("class_<id>") if they are missing.
    validator: Handle for a function that takes the loaded label map as input
      and validates it. The validator is expected to raise ValueError for an
      invalid label map. If None, uses the default validator.

  Returns:
    A dictionary mapping label names to id.

  Raises:
    ValueError: if fill_in_gaps_and_background and label_map has non-integer or
    negative values.
  """
  if isinstance(label_map_path_or_proto, string_types):
    label_map = load_labelmap(label_map_path_or_proto)
  else:
    if validator is None:
      validator = _validate_label_map
    validator(label_map_path_or_proto)
    label_map = label_map_path_or_proto

  label_map_dict = {}
  for item in label_map.item:
    if use_display_name:
      label_map_dict[item.display_name] = item.id
    else:
      label_map_dict[item.name] = item.id

  if fill_in_gaps_and_background:
    values = set(label_map_dict.values())

    if 0 not in values:
      label_map_dict['background'] = 0
    if not all(isinstance(value, int) for value in values):
      raise ValueError('The values in label map must be integers in order to'
                       'fill_in_gaps_and_background.')
    if not all(value >= 0 for value in values):
      raise ValueError('The values in the label map must be positive.')

    if len(values) != max(values) + 1:
      # there are gaps in the labels, fill in gaps.
      for value in range(1, max(values)):
        if value not in values:
          # TODO(rathodv): Add a prefix 'class_' here once the tool to generate
          # teacher annotation adds this prefix in the data.
          label_map_dict[str(value)] = value

  return label_map_dict