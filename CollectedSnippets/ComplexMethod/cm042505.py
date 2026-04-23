def hevc_index(hevc_file_name: str, allow_corrupt: bool=False) -> tuple[list, int, bytes]:
  with FileReader(hevc_file_name) as f:
    dat = f.read()

  if len(dat) < NAL_UNIT_START_CODE_SIZE + 1:
    raise VideoFileInvalid("data is too short")

  if dat[0] != 0x00:
    raise VideoFileInvalid("first byte must be 0x00")

  prefix_dat = b""
  frame_types = list()

  i = 1 # skip past first byte 0x00
  try:
    while i < len(dat):
      require_nal_unit_start(dat, i)
      nal_unit_len = get_hevc_nal_unit_length(dat, i)
      nal_unit_type = get_hevc_nal_unit_type(dat, i)
      if nal_unit_type in HEVC_PARAMETER_SET_NAL_UNITS:
        prefix_dat += dat[i:i+nal_unit_len]
      elif nal_unit_type in HEVC_CODED_SLICE_SEGMENT_NAL_UNITS:
        slice_type, is_first_slice = get_hevc_slice_type(dat, i, nal_unit_type)
        if is_first_slice:
          frame_types.append((slice_type, i))
      i += nal_unit_len
  except Exception as e:
    if not allow_corrupt:
      raise
    print(f"ERROR: NAL unit skipped @ {i}\n", str(e))

  return frame_types, len(dat), prefix_dat