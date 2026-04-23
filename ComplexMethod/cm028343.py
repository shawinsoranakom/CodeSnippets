def concatenate(boxlists, fields=None):
  """Concatenate list of BoxLists.

  This op concatenates a list of input BoxLists into a larger BoxList.  It also
  handles concatenation of BoxList fields as long as the field tensor shapes
  are equal except for the first dimension.

  Args:
    boxlists: list of BoxList objects
    fields: optional list of fields to also concatenate.  By default, all
      fields from the first BoxList in the list are included in the
      concatenation.

  Returns:
    a BoxList with number of boxes equal to
      sum([boxlist.num_boxes() for boxlist in BoxList])
  Raises:
    ValueError: if boxlists is invalid (i.e., is not a list, is empty, or
      contains non BoxList objects), or if requested fields are not contained in
      all boxlists
  """
  if not isinstance(boxlists, list):
    raise ValueError('boxlists should be a list')
  if not boxlists:
    raise ValueError('boxlists should have nonzero length')
  for boxlist in boxlists:
    if not isinstance(boxlist, np_box_list.BoxList):
      raise ValueError('all elements of boxlists should be BoxList objects')
  concatenated = np_box_list.BoxList(
      np.vstack([boxlist.get() for boxlist in boxlists]))
  if fields is None:
    fields = boxlists[0].get_extra_fields()
  for field in fields:
    first_field_shape = boxlists[0].get_field(field).shape
    first_field_shape = first_field_shape[1:]
    for boxlist in boxlists:
      if not boxlist.has_field(field):
        raise ValueError('boxlist must contain all requested fields')
      field_shape = boxlist.get_field(field).shape
      field_shape = field_shape[1:]
      if field_shape != first_field_shape:
        raise ValueError('field %s must have same shape for all boxlists '
                         'except for the 0th dimension.' % field)
    concatenated_field = np.concatenate(
        [boxlist.get_field(field) for boxlist in boxlists], axis=0)
    concatenated.add_field(field, concatenated_field)
  return concatenated