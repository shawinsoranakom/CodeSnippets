def nested_csv_str_to_json_str(csv_str):
  """Converts a nested (using '.') comma-separated k=v string to a JSON string.

  Converts a comma-separated string of key/value pairs that supports
  nesting of keys to a JSON string. Nesting is implemented using
  '.' between levels for a given key.

  Spacing between commas and = is supported (e.g. there is no difference between
  "a=1,b=2", "a = 1, b = 2", or "a=1, b=2") but there should be no spaces before
  keys or after values (e.g. " a=1,b=2" and "a=1,b=2 " are not supported).

  Note that this will only support values supported by CSV, meaning
  values such as nested lists (e.g. "a=[[1,2,3],[4,5,6]]") are not
  supported. Strings are supported as well, e.g. "a='hello'".

  An example conversion would be:

  "a=1, b=2, c.a=2, c.b=3, d.a.a=5"

  to

  "{ a: 1, b : 2, c: {a : 2, b : 3}, d: {a: {a : 5}}}"

  Args:
    csv_str: the comma separated string.

  Returns:
    the converted JSON string.

  Raises:
    ValueError: If csv_str is not in a comma separated string or
      if the string is formatted incorrectly.
  """
  if not csv_str:
    return ''

  array_param_map = collections.defaultdict(str)
  max_index_map = collections.defaultdict(str)
  formatted_entries = []
  nested_map = collections.defaultdict(list)
  pos = 0
  while pos < len(csv_str):
    m = _PARAM_RE.match(csv_str, pos)
    if not m:
      raise ValueError('Malformed hyperparameter value while parsing '
                       'CSV string: %s' % csv_str[pos:])
    pos = m.end()
    # Parse the values.
    m_dict = m.groupdict()
    name = m_dict['name']
    v = m_dict['val']
    bracketed_index = m_dict['bracketed_index']
    # If we reach the name of the array.
    if bracketed_index and '.' not in name:
      # Extract the array's index by removing '[' and ']'
      index = int(bracketed_index[1:-1])
      if '.' in v:
        numeric_val = float(v)
      else:
        numeric_val = int(v)
      # Add the value to the array.
      if name not in array_param_map:
        max_index_map[name] = index
        array_param_map[name] = [None] * (index + 1)
        array_param_map[name][index] = numeric_val
      elif index < max_index_map[name]:
        array_param_map[name][index] = numeric_val
      else:
        array_param_map[name] += [None] * (index - max_index_map[name])
        array_param_map[name][index] = numeric_val
        max_index_map[name] = index
      continue

    # If a GCS path (e.g. gs://...) is provided, wrap this in quotes
    # as yaml.load would otherwise throw an exception
    if re.match(r'(?=[^\"\'])(?=[gs://])', v):
      v = '\'{}\''.format(v)

    name_nested = name.split('.')
    if len(name_nested) > 1:
      grouping = name_nested[0]
      if bracketed_index:
        value = '.'.join(name_nested[1:]) + bracketed_index + '=' + v
      else:
        value = '.'.join(name_nested[1:]) + '=' + v
      nested_map[grouping].append(value)
    else:
      formatted_entries.append('%s : %s' % (name, v))

  for grouping, value in nested_map.items():
    value = ','.join(value)
    value = nested_csv_str_to_json_str(value)
    formatted_entries.append('%s : %s' % (grouping, value))

  # Add array parameters and check that the array is fully initialized.
  for name in array_param_map:
    if any(v is None for v in array_param_map[name]):
      raise ValueError('Did not pass all values of array: %s' % name)
    formatted_entries.append('%s : %s' % (name, array_param_map[name]))

  return '{' + ', '.join(formatted_entries) + '}'