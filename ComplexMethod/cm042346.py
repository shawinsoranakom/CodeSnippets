def _parse_install_result(response: bytes) -> dict[str, Any] | None:
  """Parse a ProfileInstallResult from an APDU response, or None if not present."""
  root = find_tag(response, TAG_PROFILE_INSTALL_RESULT)
  if not root:
    return None
  result_data = find_tag(root, TAG_INSTALL_RESULT_DATA)
  if not result_data:
    return None
  result: dict[str, Any] = {"seqNumber": 0, "success": False, "bppCommandId": None, "errorReason": None}
  notif_meta = find_tag(result_data, TAG_NOTIFICATION_METADATA)
  if notif_meta:
    seq_num = find_tag(notif_meta, TAG_STATUS)
    if seq_num:
      result["seqNumber"] = int.from_bytes(seq_num, "big")
  final_result = find_tag(result_data, 0xA2)
  if final_result:
    for tag, value in iter_tlv(final_result):
      if tag == 0xA0:
        result["success"] = True
      elif tag == 0xA1:
        bpp_cmd = find_tag(value, TAG_STATUS)
        if bpp_cmd:
          result["bppCommandId"] = int.from_bytes(bpp_cmd, "big")
        err = find_tag(value, 0x81)
        if err:
          result["errorReason"] = int.from_bytes(err, "big")
  return result