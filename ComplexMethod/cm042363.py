def parse_frame(self, frame: bytes) -> tuple[str, capnp.lib.capnp._DynamicStructBuilder] | None:
    # Quick header parse
    msg_type = int.from_bytes(frame[2:4], 'big')
    payload = frame[6:-2]
    if msg_type == 0x0107:
      body = Ubx.NavPvt.from_bytes(payload)
      return self._gen_nav_pvt(body)
    if msg_type == 0x0213:
      # Manually parse RXM-SFRBX to avoid EOF on some frames
      if len(payload) < 8:
        return None
      gnss_id = payload[0]
      sv_id = payload[1]
      freq_id = payload[3]
      num_words = payload[4]
      exp = 8 + 4 * num_words
      if exp != len(payload):
        return None
      words: list[int] = []
      off = 8
      for _ in range(num_words):
        words.append(int.from_bytes(payload[off : off + 4], 'little'))
        off += 4

      class _SfrbxView:
        def __init__(self, gid: int, sid: int, fid: int, body: list[int]):
          self.gnss_id = Ubx.GnssType(gid)
          self.sv_id = sid
          self.freq_id = fid
          self.body = body

      view = _SfrbxView(gnss_id, sv_id, freq_id, words)
      return self._gen_rxm_sfrbx(view)
    if msg_type == 0x0215:
      body = Ubx.RxmRawx.from_bytes(payload)
      return self._gen_rxm_rawx(body)
    if msg_type == 0x0A09:
      body = Ubx.MonHw.from_bytes(payload)
      return self._gen_mon_hw(body)
    if msg_type == 0x0A0B:
      body = Ubx.MonHw2.from_bytes(payload)
      return self._gen_mon_hw2(body)
    if msg_type == 0x0135:
      body = Ubx.NavSat.from_bytes(payload)
      return self._gen_nav_sat(body)
    return None