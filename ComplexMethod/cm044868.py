def mask_silence(mag, ref, thres=0.2, min_range=64, fade_size=32):
    if min_range < fade_size * 2:
        raise ValueError("min_range must be >= fade_area * 2")

    mag = mag.copy()

    idx = np.where(ref.mean(axis=(0, 1)) < thres)[0]
    starts = np.insert(idx[np.where(np.diff(idx) != 1)[0] + 1], 0, idx[0])
    ends = np.append(idx[np.where(np.diff(idx) != 1)[0]], idx[-1])
    uninformative = np.where(ends - starts > min_range)[0]
    if len(uninformative) > 0:
        starts = starts[uninformative]
        ends = ends[uninformative]
        old_e = None
        for s, e in zip(starts, ends):
            if old_e is not None and s - old_e < fade_size:
                s = old_e - fade_size * 2

            if s != 0:
                weight = np.linspace(0, 1, fade_size)
                mag[:, :, s : s + fade_size] += weight * ref[:, :, s : s + fade_size]
            else:
                s -= fade_size

            if e != mag.shape[2]:
                weight = np.linspace(1, 0, fade_size)
                mag[:, :, e - fade_size : e] += weight * ref[:, :, e - fade_size : e]
            else:
                e += fade_size

            mag[:, :, s + fade_size : e - fade_size] += ref[:, :, s + fade_size : e - fade_size]
            old_e = e

    return mag