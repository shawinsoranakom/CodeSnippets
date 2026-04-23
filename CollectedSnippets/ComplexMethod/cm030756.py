def stats(cls, start_year=1):
        count = gap_count = fold_count = zeros_count = 0
        min_gap = min_fold = timedelta.max
        max_gap = max_fold = ZERO
        min_gap_datetime = max_gap_datetime = datetime.min
        min_gap_zone = max_gap_zone = None
        min_fold_datetime = max_fold_datetime = datetime.min
        min_fold_zone = max_fold_zone = None
        stats_since = datetime(start_year, 1, 1) # Starting from 1970 eliminates a lot of noise
        for zonename in cls.zonenames():
            count += 1
            tz = cls.fromname(zonename)
            for dt, shift in tz.transitions():
                if dt < stats_since:
                    continue
                if shift > ZERO:
                    gap_count += 1
                    if (shift, dt) > (max_gap, max_gap_datetime):
                        max_gap = shift
                        max_gap_zone = zonename
                        max_gap_datetime = dt
                    if (shift, datetime.max - dt) < (min_gap, datetime.max - min_gap_datetime):
                        min_gap = shift
                        min_gap_zone = zonename
                        min_gap_datetime = dt
                elif shift < ZERO:
                    fold_count += 1
                    shift = -shift
                    if (shift, dt) > (max_fold, max_fold_datetime):
                        max_fold = shift
                        max_fold_zone = zonename
                        max_fold_datetime = dt
                    if (shift, datetime.max - dt) < (min_fold, datetime.max - min_fold_datetime):
                        min_fold = shift
                        min_fold_zone = zonename
                        min_fold_datetime = dt
                else:
                    zeros_count += 1
        trans_counts = (gap_count, fold_count, zeros_count)
        print("Number of zones:       %5d" % count)
        print("Number of transitions: %5d = %d (gaps) + %d (folds) + %d (zeros)" %
              ((sum(trans_counts),) + trans_counts))
        print("Min gap:         %16s at %s in %s" % (min_gap, min_gap_datetime, min_gap_zone))
        print("Max gap:         %16s at %s in %s" % (max_gap, max_gap_datetime, max_gap_zone))
        print("Min fold:        %16s at %s in %s" % (min_fold, min_fold_datetime, min_fold_zone))
        print("Max fold:        %16s at %s in %s" % (max_fold, max_fold_datetime, max_fold_zone))