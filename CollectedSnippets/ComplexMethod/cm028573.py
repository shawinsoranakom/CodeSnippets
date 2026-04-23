def inference(img_file: str, model: tf_keras.layers.Layer) -> Dict[str, Any]:
  """Inference step."""
  img = cv2.cvtColor(cv2.imread(img_file), cv2.COLOR_BGR2RGB)
  img_ndarray, ratio = _preprocess(img)

  output_dict = model.serve(img_ndarray)
  class_tensor = output_dict['classes'].numpy()
  mask_tensor = output_dict['masks'].numpy()
  group_tensor = output_dict['groups'].numpy()

  indices = np.where(class_tensor[0])[0].tolist()  # indices of positive slots.
  mask_list = [
      mask_tensor[0, :, :, index] for index in indices]  # List of mask ndarray.

  # Form lines and words
  lines = []
  line_indices = []
  for index, mask in tqdm.tqdm(zip(indices, mask_list)):
    line = {
        'words': [],
        'text': '',
    }

    contours, _ = cv2.findContours(
        (mask > 0.).astype(np.uint8),
        cv2.RETR_TREE,
        cv2.CHAIN_APPROX_SIMPLE)[-2:]
    for contour in contours:
      if (isinstance(contour, np.ndarray) and
          len(contour.shape) == 3 and
          contour.shape[0] > 2 and
          contour.shape[1] == 1 and
          contour.shape[2] == 2):
        cnt_list = (contour[:, 0] * ratio).astype(np.int32).tolist()
        line['words'].append({'text': '', 'vertices': cnt_list})
      else:
        logging.error('Invalid contour: %s, discarded', str(contour))
    if line['words']:
      lines.append(line)
      line_indices.append(index)

  # Form paragraphs
  line_grouping = utilities.DisjointSet(len(line_indices))
  affinity = group_tensor[0][line_indices][:, line_indices]
  for i1, i2 in zip(*np.where(affinity > _PARA_GROUP_THR)):
    line_grouping.union(i1, i2)

  line_groups = line_grouping.to_group()
  paragraphs = []
  for line_group in line_groups:
    paragraph = {'lines': []}
    for id_ in line_group:
      paragraph['lines'].append(lines[id_])
    if paragraph:
      paragraphs.append(paragraph)

  return paragraphs