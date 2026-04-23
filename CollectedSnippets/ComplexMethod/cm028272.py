def read_annotation_file(filename):
  """Reads a KITTI annotation file.

  Converts a KITTI annotation file into a dictionary containing all the
  relevant information.

  Args:
    filename: the path to the annotataion text file.

  Returns:
    anno: A dictionary with the converted annotation information. See annotation
    README file for details on the different fields.
  """
  with open(filename) as f:
    content = f.readlines()
  content = [x.strip().split(' ') for x in content]

  anno = {}
  anno['type'] = np.array([x[0].lower() for x in content])
  anno['truncated'] = np.array([float(x[1]) for x in content])
  anno['occluded'] = np.array([int(x[2]) for x in content])
  anno['alpha'] = np.array([float(x[3]) for x in content])

  anno['2d_bbox_left'] = np.array([float(x[4]) for x in content])
  anno['2d_bbox_top'] = np.array([float(x[5]) for x in content])
  anno['2d_bbox_right'] = np.array([float(x[6]) for x in content])
  anno['2d_bbox_bottom'] = np.array([float(x[7]) for x in content])

  anno['3d_bbox_height'] = np.array([float(x[8]) for x in content])
  anno['3d_bbox_width'] = np.array([float(x[9]) for x in content])
  anno['3d_bbox_length'] = np.array([float(x[10]) for x in content])
  anno['3d_bbox_x'] = np.array([float(x[11]) for x in content])
  anno['3d_bbox_y'] = np.array([float(x[12]) for x in content])
  anno['3d_bbox_z'] = np.array([float(x[13]) for x in content])
  anno['3d_bbox_rot_y'] = np.array([float(x[14]) for x in content])

  return anno