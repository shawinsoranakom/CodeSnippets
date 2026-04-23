def match_files(input_path: Union[Sequence[str], str]) -> List[str]:
  """Matches files from an input_path."""
  matched_files = []
  # Read dataset from files.
  usage = ('`input_path` should be either (1) a str indicating a file '
           'path/pattern, or (2) a str indicating multiple file '
           'paths/patterns separated by comma (e.g "a, b, c" or no spaces '
           '"a,b,c", or (3) a list of str, each of which is a file '
           'path/pattern or multiple file paths/patterns separated by '
           'comma, but got: %s')
  if isinstance(input_path, str):
    input_path_list = [input_path]
  elif isinstance(input_path, (list, tuple)):
    if any(not isinstance(x, str) for x in input_path):
      raise ValueError(usage % input_path)
    input_path_list = input_path
  else:
    raise ValueError(usage % input_path)

  for input_path in input_path_list:
    input_patterns = input_path.strip().split(',')
    for input_pattern in input_patterns:
      input_pattern = input_pattern.strip()
      if not input_pattern:
        continue
      if '*' in input_pattern or '?' in input_pattern:
        tmp_matched_files = tf.io.gfile.glob(input_pattern)
        if not tmp_matched_files:
          raise ValueError('%s does not match any files.' % input_pattern)
        matched_files.extend(tmp_matched_files)
      else:
        matched_files.append(input_pattern)

  if not matched_files:
    raise ValueError('%s does not match any files.' % input_path)

  return matched_files