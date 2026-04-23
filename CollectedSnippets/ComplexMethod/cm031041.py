def construct_zone(self, transitions, after=None, version=3):
        # These are not used for anything, so we're not going to include
        # them for now.
        isutc = []
        isstd = []
        leap_seconds = []

        offset_lists = [[], []]
        trans_times_lists = [[], []]
        trans_idx_lists = [[], []]

        v1_range = (-(2 ** 31), 2 ** 31)
        v2_range = (-(2 ** 63), 2 ** 63)
        ranges = [v1_range, v2_range]

        def zt_as_tuple(zt):
            # zt may be a tuple (timestamp, offset_before, offset_after) or
            # a ZoneTransition object — this is to allow the timestamp to be
            # values that are outside the valid range for datetimes but still
            # valid 64-bit timestamps.
            if isinstance(zt, tuple):
                return zt

            if zt.transition:
                trans_time = int(zt.transition_utc.timestamp())
            else:
                trans_time = None

            return (trans_time, zt.offset_before, zt.offset_after)

        transitions = sorted(map(zt_as_tuple, transitions), key=lambda x: x[0])

        for zt in transitions:
            trans_time, offset_before, offset_after = zt

            for v, (dt_min, dt_max) in enumerate(ranges):
                offsets = offset_lists[v]
                trans_times = trans_times_lists[v]
                trans_idx = trans_idx_lists[v]

                if trans_time is not None and not (
                    dt_min <= trans_time <= dt_max
                ):
                    continue

                if offset_before not in offsets:
                    offsets.append(offset_before)

                if offset_after not in offsets:
                    offsets.append(offset_after)

                if trans_time is not None:
                    trans_times.append(trans_time)
                    trans_idx.append(offsets.index(offset_after))

        isutcnt = len(isutc)
        isstdcnt = len(isstd)
        leapcnt = len(leap_seconds)

        zonefile = io.BytesIO()

        time_types = ("l", "q")
        for v in range(min((version, 2))):
            offsets = offset_lists[v]
            trans_times = trans_times_lists[v]
            trans_idx = trans_idx_lists[v]
            time_type = time_types[v]

            # Translate the offsets into something closer to the C values
            abbrstr = bytearray()
            ttinfos = []

            for offset in offsets:
                utcoff = int(offset.utcoffset.total_seconds())
                isdst = bool(offset.dst)
                abbrind = len(abbrstr)

                ttinfos.append((utcoff, isdst, abbrind))
                abbrstr += offset.tzname.encode("ascii") + b"\x00"
            abbrstr = bytes(abbrstr)

            typecnt = len(offsets)
            timecnt = len(trans_times)
            charcnt = len(abbrstr)

            # Write the header
            zonefile.write(b"TZif")
            zonefile.write(b"%d" % version)
            zonefile.write(b" " * 15)
            zonefile.write(
                struct.pack(
                    ">6l", isutcnt, isstdcnt, leapcnt, timecnt, typecnt, charcnt
                )
            )

            # Now the transition data
            zonefile.write(struct.pack(f">{timecnt}{time_type}", *trans_times))
            zonefile.write(struct.pack(f">{timecnt}B", *trans_idx))

            for ttinfo in ttinfos:
                zonefile.write(struct.pack(">lbb", *ttinfo))

            zonefile.write(bytes(abbrstr))

            # Now the metadata and leap seconds
            zonefile.write(struct.pack(f"{isutcnt}b", *isutc))
            zonefile.write(struct.pack(f"{isstdcnt}b", *isstd))
            zonefile.write(struct.pack(f">{leapcnt}l", *leap_seconds))

            # Finally we write the TZ string if we're writing a Version 2+ file
            if v > 0:
                zonefile.write(b"\x0A")
                zonefile.write(after.encode("ascii"))
                zonefile.write(b"\x0A")

        zonefile.seek(0)
        return zonefile