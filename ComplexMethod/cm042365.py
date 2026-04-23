def _parse_glonass_ephemeris(self, msg: Ubx.RxmSfrbx) -> tuple[str, capnp.lib.capnp._DynamicStructBuilder] | None:
    # words are 4 bytes each; Glonass parser expects 16 bytes (string)
    body = msg.body
    if len(body) != 4:
      return None
    string_bytes = bytearray()
    for word in body:
      for i in (3, 2, 1, 0):
        string_bytes.append((word >> (8 * i)) & 0xFF)

    gl = Glonass.from_bytes(bytes(string_bytes))
    string_number = gl.string_number
    if string_number < 1 or string_number > 5 or gl.idle_chip:
      return None

    # correlate by superframe and timing, similar to C++ logic
    freq_id = msg.freq_id
    superframe_unknown = False
    needs_clear = False
    for i in range(1, 6):
      if i not in self.caches.glonass_strings[freq_id]:
        continue
      sf_prev = self.caches.glonass_string_superframes[freq_id].get(i, 0)
      if sf_prev == 0 or gl.superframe_number == 0:
        superframe_unknown = True
      elif sf_prev != gl.superframe_number:
        needs_clear = True
      if superframe_unknown:
        prev_time = self.caches.glonass_string_times[freq_id].get(i, 0.0)
        if abs((prev_time - 2.0 * i) - (self.framer.last_log_time - 2.0 * string_number)) > 10:
          needs_clear = True

    if needs_clear:
      self.caches.glonass_strings[freq_id].clear()
      self.caches.glonass_string_superframes[freq_id].clear()
      self.caches.glonass_string_times[freq_id].clear()

    self.caches.glonass_strings[freq_id][string_number] = bytes(string_bytes)
    self.caches.glonass_string_superframes[freq_id][string_number] = gl.superframe_number
    self.caches.glonass_string_times[freq_id][string_number] = self.framer.last_log_time

    if msg.sv_id == 255:
      # unknown SV id
      return None
    if len(self.caches.glonass_strings[freq_id]) != 5:
      return None

    dat = messaging.new_message('ubloxGnss', valid=True)
    eph = dat.ubloxGnss.init('glonassEphemeris')
    eph.svId = msg.sv_id
    eph.freqNum = msg.freq_id - 7

    current_day = 0
    tk = 0

    # string 1
    try:
      s1 = Glonass.from_bytes(self.caches.glonass_strings[freq_id][1]).data
    except Exception:
      return None
    assert isinstance(s1, Glonass.String1)
    eph.p1 = int(s1.p1)
    tk = int(s1.t_k)
    eph.deprecated.tk = tk
    eph.xVel = float(s1.x_vel) * math.pow(2, -20)
    eph.xAccel = float(s1.x_accel) * math.pow(2, -30)
    eph.x = float(s1.x) * math.pow(2, -11)

    # string 2
    try:
      s2 = Glonass.from_bytes(self.caches.glonass_strings[freq_id][2]).data
    except Exception:
      return None
    assert isinstance(s2, Glonass.String2)
    eph.svHealth = int(s2.b_n >> 2)
    eph.p2 = int(s2.p2)
    eph.tb = int(s2.t_b)
    eph.yVel = float(s2.y_vel) * math.pow(2, -20)
    eph.yAccel = float(s2.y_accel) * math.pow(2, -30)
    eph.y = float(s2.y) * math.pow(2, -11)

    # string 3
    try:
      s3 = Glonass.from_bytes(self.caches.glonass_strings[freq_id][3]).data
    except Exception:
      return None
    assert isinstance(s3, Glonass.String3)
    eph.p3 = int(s3.p3)
    eph.gammaN = float(s3.gamma_n) * math.pow(2, -40)
    eph.svHealth = int(eph.svHealth | (1 if s3.l_n else 0))
    eph.zVel = float(s3.z_vel) * math.pow(2, -20)
    eph.zAccel = float(s3.z_accel) * math.pow(2, -30)
    eph.z = float(s3.z) * math.pow(2, -11)

    # string 4
    try:
      s4 = Glonass.from_bytes(self.caches.glonass_strings[freq_id][4]).data
    except Exception:
      return None
    assert isinstance(s4, Glonass.String4)
    current_day = int(s4.n_t)
    eph.nt = current_day
    eph.tauN = float(s4.tau_n) * math.pow(2, -30)
    eph.deltaTauN = float(s4.delta_tau_n) * math.pow(2, -30)
    eph.age = int(s4.e_n)
    eph.p4 = int(s4.p4)
    eph.svURA = float(self.glonass_URA_lookup.get(int(s4.f_t), 0.0))
    # consistency check: SV slot number
    # if it doesn't match, keep going but note mismatch (no logging here)
    eph.svType = int(s4.m)

    # string 5
    try:
      s5 = Glonass.from_bytes(self.caches.glonass_strings[freq_id][5]).data
    except Exception:
      return None
    assert isinstance(s5, Glonass.String5)
    eph.n4 = int(s5.n_4)
    tk_seconds = int(SECS_IN_HR * ((tk >> 7) & 0x1F) + SECS_IN_MIN * ((tk >> 1) & 0x3F) + (tk & 0x1) * 30)
    eph.tkSeconds = tk_seconds

    self.caches.glonass_strings[freq_id].clear()
    return ('ubloxGnss', dat)