def _transform_csv(input_path, output_path, names, skip_first, separator=","):
  """Transform csv to a regularized format.

  Args:
    input_path: The path of the raw csv.
    output_path: The path of the cleaned csv.
    names: The csv column names.
    skip_first: Boolean of whether to skip the first line of the raw csv.
    separator: Character used to separate fields in the raw csv.
  """
  if six.PY2:
    names = [six.ensure_text(n, "utf-8") for n in names]

  with tf.io.gfile.GFile(output_path, "wb") as f_out, \
      tf.io.gfile.GFile(input_path, "rb") as f_in:

    # Write column names to the csv.
    f_out.write(",".join(names).encode("utf-8"))
    f_out.write(b"\n")
    for i, line in enumerate(f_in):
      if i == 0 and skip_first:
        continue  # ignore existing labels in the csv

      line = six.ensure_text(line, "utf-8", errors="ignore")
      fields = line.split(separator)
      if separator != ",":
        fields = ['"{}"'.format(field) if "," in field else field
                  for field in fields]
      f_out.write(",".join(fields).encode("utf-8"))