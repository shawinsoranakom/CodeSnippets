def _get_segments_local(self, data_dir):
    files = os.listdir(data_dir)
    segment_files = defaultdict(list)

    for f in files:
      fullpath = os.path.join(data_dir, f)
      explorer_match = re.match(RE.EXPLORER_FILE, f)
      op_match = re.match(RE.OP_SEGMENT_DIR, f)

      if explorer_match:
        segment_name = explorer_match.group('segment_name')
        fn = explorer_match.group('file_name')
        if segment_name.replace('_', '|').startswith(self.name.canonical_name):
          segment_files[segment_name].append((fullpath, fn))
      elif op_match and os.path.isdir(fullpath):
        segment_name = op_match.group('segment_name')
        if segment_name.startswith(self.name.canonical_name):
          for seg_f in os.listdir(fullpath):
            segment_files[segment_name].append((os.path.join(fullpath, seg_f), seg_f))
      elif f == self.name.canonical_name:
        for seg_num in os.listdir(fullpath):
          if not seg_num.isdigit():
            continue

          segment_name = f'{self.name.canonical_name}--{seg_num}'
          for seg_f in os.listdir(os.path.join(fullpath, seg_num)):
            segment_files[segment_name].append((os.path.join(fullpath, seg_num, seg_f), seg_f))

    segments = []
    for segment, files in segment_files.items():

      try:
        log_path = next(path for path, filename in files if filename in FileName.RLOG)
      except StopIteration:
        log_path = None

      try:
        qlog_path = next(path for path, filename in files if filename in FileName.QLOG)
      except StopIteration:
        qlog_path = None

      try:
        camera_path = next(path for path, filename in files if filename in FileName.FCAMERA)
      except StopIteration:
        camera_path = None

      try:
        dcamera_path = next(path for path, filename in files if filename in FileName.DCAMERA)
      except StopIteration:
        dcamera_path = None

      try:
        ecamera_path = next(path for path, filename in files if filename in FileName.ECAMERA)
      except StopIteration:
        ecamera_path = None

      try:
        qcamera_path = next(path for path, filename in files if filename in FileName.QCAMERA)
      except StopIteration:
        qcamera_path = None

      segments.append(Segment(segment, log_path, qlog_path, camera_path, dcamera_path, ecamera_path, qcamera_path))

    if len(segments) == 0:
      raise ValueError(f'Could not find segments for route {self.name.canonical_name} in data directory {data_dir}')
    return sorted(segments, key=lambda seg: seg.name.segment_num)