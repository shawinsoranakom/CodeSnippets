def compare_elements(elem_list1, elem_list2):
  if len(elem_list1) != len(elem_list2):
    return False

  for elem1, elem2 in zip(elem_list1, elem_list2):
    for key in elem1:
      if key not in elem2:
        return False
      if isinstance(elem1[key], np.ndarray) or isinstance(
          elem2[key], np.ndarray
      ):
        if not np.array_equal(elem1[key], elem2[key]):
          return False
      else:
        if elem1[key] != elem2[key]:
          return False

  return True