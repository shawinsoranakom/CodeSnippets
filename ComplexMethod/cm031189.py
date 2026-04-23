def _utcoff_to_dstoff(trans_idx, utcoffsets, isdsts):
        # Now we must transform our ttis and abbrs into `_ttinfo` objects,
        # but there is an issue: .dst() must return a timedelta with the
        # difference between utcoffset() and the "standard" offset, but
        # the "base offset" and "DST offset" are not encoded in the file;
        # we can infer what they are from the isdst flag, but it is not
        # sufficient to just look at the last standard offset, because
        # occasionally countries will shift both DST offset and base offset.

        typecnt = len(isdsts)
        dstoffs = [0] * typecnt  # Provisionally assign all to 0.
        dst_cnt = sum(isdsts)
        dst_found = 0

        for i in range(1, len(trans_idx)):
            if dst_cnt == dst_found:
                break

            idx = trans_idx[i]

            dst = isdsts[idx]

            # We're only going to look at daylight saving time
            if not dst:
                continue

            # Skip any offsets that have already been assigned
            if dstoffs[idx] != 0:
                continue

            dstoff = 0
            utcoff = utcoffsets[idx]

            comp_idx = trans_idx[i - 1]

            if not isdsts[comp_idx]:
                dstoff = utcoff - utcoffsets[comp_idx]

            if not dstoff and idx < (typecnt - 1) and i + 1 < len(trans_idx):
                comp_idx = trans_idx[i + 1]

                # If the following transition is also DST and we couldn't
                # find the DST offset by this point, we're going to have to
                # skip it and hope this transition gets assigned later
                if isdsts[comp_idx]:
                    continue

                dstoff = utcoff - utcoffsets[comp_idx]

            if dstoff:
                dst_found += 1
                dstoffs[idx] = dstoff
        else:
            # If we didn't find a valid value for a given index, we'll end up
            # with dstoff = 0 for something where `isdst=1`. This is obviously
            # wrong - one hour will be a much better guess than 0
            for idx in range(typecnt):
                if not dstoffs[idx] and isdsts[idx]:
                    dstoffs[idx] = 3600

        return dstoffs