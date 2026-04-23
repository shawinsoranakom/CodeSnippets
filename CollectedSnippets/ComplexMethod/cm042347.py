def load_bpp(client: AtClient, b64_bpp: str) -> dict:
  bpp = b64d(b64_bpp)
  result = None
  for chunk in _split_bpp(bpp):
    response = es10x_command(client, chunk)
    if response:
      result = _parse_install_result(response) or result

  if result is None:
    raise RuntimeError("Profile installation failed: no result from eUICC")
  if not result["success"] and result["errorReason"] is not None:
    msg = BPP_ERROR_MESSAGES.get(result["errorReason"])
    if not msg:
      cmd_name = BPP_COMMAND_NAMES.get(result["bppCommandId"], f"unknown({result['bppCommandId']})")
      err_name = BPP_ERROR_REASONS.get(result["errorReason"], f"unknown({result['errorReason']})")
      msg = f"Profile installation failed at {cmd_name}: {err_name}"
    raise RuntimeError(msg)
  if not result["success"]:
    raise RuntimeError("Profile installation failed: no result from eUICC")
  return result