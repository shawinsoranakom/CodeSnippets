def _get_segments_remote(self):
    api = CommaApi(get_token())
    route_files = api.get('v1/route/' + self.name.canonical_name + '/files')
    self.files = list(chain.from_iterable(route_files.values()))

    segments = {}
    for url in self.files:
      _, dongle_id, time_str, segment_num, fn = urlparse(url).path.rsplit('/', maxsplit=4)
      segment_name = f'{dongle_id}|{time_str}--{segment_num}'
      if segments.get(segment_name):
        segments[segment_name] = Segment(
          segment_name,
          url if fn in FileName.RLOG else segments[segment_name].log_path,
          url if fn in FileName.QLOG else segments[segment_name].qlog_path,
          url if fn in FileName.FCAMERA else segments[segment_name].camera_path,
          url if fn in FileName.DCAMERA else segments[segment_name].dcamera_path,
          url if fn in FileName.ECAMERA else segments[segment_name].ecamera_path,
          url if fn in FileName.QCAMERA else segments[segment_name].qcamera_path,
        )
      else:
        segments[segment_name] = Segment(
          segment_name,
          url if fn in FileName.RLOG else None,
          url if fn in FileName.QLOG else None,
          url if fn in FileName.FCAMERA else None,
          url if fn in FileName.DCAMERA else None,
          url if fn in FileName.ECAMERA else None,
          url if fn in FileName.QCAMERA else None,
        )

    return sorted(segments.values(), key=lambda seg: seg.name.segment_num)