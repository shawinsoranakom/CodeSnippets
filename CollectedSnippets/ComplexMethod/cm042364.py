def _parse_gps_ephemeris(self, msg: Ubx.RxmSfrbx) -> tuple[str, capnp.lib.capnp._DynamicStructBuilder] | None:
    # body is list of 10 words; convert to 30-byte subframe (strip parity/padding)
    body = msg.body
    if len(body) != 10:
      return None
    subframe_data = bytearray()
    for word in body:
      word >>= 6
      subframe_data.append((word >> 16) & 0xFF)
      subframe_data.append((word >> 8) & 0xFF)
      subframe_data.append(word & 0xFF)

    sf = Gps.from_bytes(bytes(subframe_data))
    subframe_id = sf.how.subframe_id
    if subframe_id < 1 or subframe_id > 3:
      return None
    self.caches.gps_subframes[msg.sv_id][subframe_id] = bytes(subframe_data)

    if len(self.caches.gps_subframes[msg.sv_id]) != 3:
      return None

    dat = messaging.new_message('ubloxGnss', valid=True)
    eph = dat.ubloxGnss.init('ephemeris')
    eph.svId = msg.sv_id

    iode_s2 = 0
    iode_s3 = 0
    iodc_lsb = 0
    week = 0

    # Subframe 1
    sf1 = Gps.from_bytes(self.caches.gps_subframes[msg.sv_id][1])
    s1 = sf1.body
    assert isinstance(s1, Gps.Subframe1)
    week = s1.week_no
    week += 1024
    if week < 1877:
      week += 1024
    eph.tgd = s1.t_gd * math.pow(2, -31)
    eph.toc = s1.t_oc * math.pow(2, 4)
    eph.af2 = s1.af_2 * math.pow(2, -55)
    eph.af1 = s1.af_1 * math.pow(2, -43)
    eph.af0 = s1.af_0 * math.pow(2, -31)
    eph.svHealth = s1.sv_health
    eph.towCount = sf1.how.tow_count
    iodc_lsb = s1.iodc_lsb

    # Subframe 2
    sf2 = Gps.from_bytes(self.caches.gps_subframes[msg.sv_id][2])
    s2 = sf2.body
    assert isinstance(s2, Gps.Subframe2)
    if s2.t_oe == 0 and sf2.how.tow_count * 6 >= (SECS_IN_WEEK - 2 * SECS_IN_HR):
      week += 1
    eph.crs = s2.c_rs * math.pow(2, -5)
    eph.deltaN = s2.delta_n * math.pow(2, -43) * self.gpsPi
    eph.m0 = s2.m_0 * math.pow(2, -31) * self.gpsPi
    eph.cuc = s2.c_uc * math.pow(2, -29)
    eph.ecc = s2.e * math.pow(2, -33)
    eph.cus = s2.c_us * math.pow(2, -29)
    eph.a = math.pow(s2.sqrt_a * math.pow(2, -19), 2.0)
    eph.toe = s2.t_oe * math.pow(2, 4)
    iode_s2 = s2.iode

    # Subframe 3
    sf3 = Gps.from_bytes(self.caches.gps_subframes[msg.sv_id][3])
    s3 = sf3.body
    assert isinstance(s3, Gps.Subframe3)
    eph.cic = s3.c_ic * math.pow(2, -29)
    eph.omega0 = s3.omega_0 * math.pow(2, -31) * self.gpsPi
    eph.cis = s3.c_is * math.pow(2, -29)
    eph.i0 = s3.i_0 * math.pow(2, -31) * self.gpsPi
    eph.crc = s3.c_rc * math.pow(2, -5)
    eph.omega = s3.omega * math.pow(2, -31) * self.gpsPi
    eph.omegaDot = s3.omega_dot * math.pow(2, -43) * self.gpsPi
    eph.iode = s3.iode
    eph.iDot = s3.idot * math.pow(2, -43) * self.gpsPi
    iode_s3 = s3.iode

    eph.toeWeek = week
    eph.tocWeek = week

    # clear cache for this SV
    self.caches.gps_subframes[msg.sv_id].clear()
    if not (iodc_lsb == iode_s2 == iode_s3):
      return None
    return ('ubloxGnss', dat)