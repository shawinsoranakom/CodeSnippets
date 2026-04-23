def boolean_mask(boxlist,
                 indicator,
                 fields=None,
                 scope=None,
                 use_static_shapes=False,
                 indicator_sum=None):
  """Select boxes from BoxList according to indicator and return new BoxList.

  `boolean_mask` returns the subset of boxes that are marked as "True" by the
  indicator tensor. By default, `boolean_mask` returns boxes corresponding to
  the input index list, as well as all additional fields stored in the boxlist
  (indexing into the first dimension).  However one can optionally only draw
  from a subset of fields.

  Args:
    boxlist: BoxList holding N boxes
    indicator: a rank-1 boolean tensor
    fields: (optional) list of fields to also gather from.  If None (default),
      all fields are gathered from.  Pass an empty fields list to only gather
      the box coordinates.
    scope: name scope.
    use_static_shapes: Whether to use an implementation with static shape
      gurantees.
    indicator_sum: An integer containing the sum of `indicator` vector. Only
      required if `use_static_shape` is True.

  Returns:
    subboxlist: a BoxList corresponding to the subset of the input BoxList
      specified by indicator
  Raises:
    ValueError: if `indicator` is not a rank-1 boolean tensor.
  """
  with tf.name_scope(scope or 'BooleanMask'):
    if indicator.shape.ndims != 1:
      raise ValueError('indicator should have rank 1')
    if indicator.dtype != tf.bool:
      raise ValueError('indicator should be a boolean tensor')
    if use_static_shapes:
      if not (indicator_sum and isinstance(indicator_sum, int)):
        raise ValueError('`indicator_sum` must be a of type int')
      selected_positions = tf.cast(indicator, dtype=tf.float32)
      indexed_positions = tf.cast(
          tf.multiply(tf.cumsum(selected_positions), selected_positions),
          dtype=tf.int32)
      one_hot_selector = tf.one_hot(
          indexed_positions - 1, indicator_sum, dtype=tf.float32)
      sampled_indices = tf.cast(
          tf.tensordot(
              tf.cast(tf.range(tf.shape(indicator)[0]), dtype=tf.float32),
              one_hot_selector,
              axes=[0, 0]),
          dtype=tf.int32)
      return gather(boxlist, sampled_indices, use_static_shapes=True)
    else:
      subboxlist = box_list.BoxList(tf.boolean_mask(boxlist.get(), indicator))
      if fields is None:
        fields = boxlist.get_extra_fields()
      for field in fields:
        if not boxlist.has_field(field):
          raise ValueError('boxlist must contain all specified fields')
        subfieldlist = tf.boolean_mask(boxlist.get_field(field), indicator)
        subboxlist.add_field(field, subfieldlist)
      return subboxlist