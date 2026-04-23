def multicrop_pic(image: Image, mindim, maxdim, minarea, maxarea, objective, threshold):
    iw, ih = image.size
    err = lambda w, h: 1 - (lambda x: x if x < 1 else 1 / x)(iw / ih / (w / h))
    wh = max(((w, h) for w in range(mindim, maxdim + 1, 64) for h in range(mindim, maxdim + 1, 64)
              if minarea <= w * h <= maxarea and err(w, h) <= threshold),
             key=lambda wh: (wh[0] * wh[1], -err(*wh))[::1 if objective == 'Maximize area' else -1],
             default=None
             )
    return wh and center_crop(image, *wh)