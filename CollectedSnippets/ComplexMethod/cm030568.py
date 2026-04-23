def tryone_inner(tag, nbins, hashes, expected=None, zlimit=None):
            from collections import Counter

            nballs = len(hashes)
            mean, sdev = support.collision_stats(nbins, nballs)
            c = Counter(hashes)
            collisions = nballs - len(c)
            z = (collisions - mean) / sdev
            pileup = max(c.values()) - 1
            del c
            got = (collisions, pileup)
            failed = False
            prefix = ""
            if zlimit is not None and z > zlimit:
                failed = True
                prefix = f"FAIL z > {zlimit}; "
            if expected is not None and got != expected:
                failed = True
                prefix += f"FAIL {got} != {expected}; "
            if failed or JUST_SHOW_HASH_RESULTS:
                msg = f"{prefix}{tag}; pileup {pileup:,} mean {mean:.1f} "
                msg += f"coll {collisions:,} z {z:+.1f}"
                if JUST_SHOW_HASH_RESULTS:
                    import sys
                    print(msg, file=sys.__stdout__)
                else:
                    self.fail(msg)