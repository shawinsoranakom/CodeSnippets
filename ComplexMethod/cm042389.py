def setup_logs(diag, types_to_log):
  opcode, payload = send_recv(diag, DIAG_LOG_CONFIG_F, pack('<3xI', LOG_CONFIG_RETRIEVE_ID_RANGES_OP))

  header_spec = '<3xII'
  operation, status = unpack_from(header_spec, payload)
  assert operation == LOG_CONFIG_RETRIEVE_ID_RANGES_OP
  assert status == LOG_CONFIG_SUCCESS_S

  log_masks = unpack_from('<16I', payload, calcsize(header_spec))

  for log_type, log_mask_bitsize in enumerate(log_masks):
    if log_mask_bitsize:
      log_mask = [0] * ((log_mask_bitsize+7)//8)
      for i in range(log_mask_bitsize):
        if ((log_type<<12)|i) in types_to_log:
          log_mask[i//8] |= 1 << (i%8)
      opcode, payload = send_recv(diag, DIAG_LOG_CONFIG_F, pack('<3xIII',
          LOG_CONFIG_SET_MASK_OP,
          log_type,
          log_mask_bitsize
      ) + bytes(log_mask))
      assert opcode == DIAG_LOG_CONFIG_F
      operation, status = unpack_from(header_spec, payload)
      assert operation == LOG_CONFIG_SET_MASK_OP
      assert status == LOG_CONFIG_SUCCESS_S