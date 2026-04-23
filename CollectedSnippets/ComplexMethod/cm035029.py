def __call__(self, data):
        imgs = data["image"]

        h, w = imgs[0].shape[0:2]
        t_w, t_h = self.target_size
        p_w, p_h = self.target_size
        if w == t_w and h == t_h:
            return data

        t_h = t_h if t_h < h else h
        t_w = t_w if t_w < w else w

        if random.random() > 3.0 / 8.0 and np.max(imgs[1]) > 0:
            # make sure to crop the text region
            tl = np.min(np.where(imgs[1] > 0), axis=1) - (t_h, t_w)
            tl[tl < 0] = 0
            br = np.max(np.where(imgs[1] > 0), axis=1) - (t_h, t_w)
            br[br < 0] = 0
            br[0] = min(br[0], h - t_h)
            br[1] = min(br[1], w - t_w)

            i = random.randint(tl[0], br[0]) if tl[0] < br[0] else 0
            j = random.randint(tl[1], br[1]) if tl[1] < br[1] else 0
        else:
            i = random.randint(0, h - t_h) if h - t_h > 0 else 0
            j = random.randint(0, w - t_w) if w - t_w > 0 else 0

        n_imgs = []
        for idx in range(len(imgs)):
            if len(imgs[idx].shape) == 3:
                s3_length = int(imgs[idx].shape[-1])
                img = imgs[idx][i : i + t_h, j : j + t_w, :]
                img_p = cv2.copyMakeBorder(
                    img,
                    0,
                    p_h - t_h,
                    0,
                    p_w - t_w,
                    borderType=cv2.BORDER_CONSTANT,
                    value=tuple(0 for i in range(s3_length)),
                )
            else:
                img = imgs[idx][i : i + t_h, j : j + t_w]
                img_p = cv2.copyMakeBorder(
                    img,
                    0,
                    p_h - t_h,
                    0,
                    p_w - t_w,
                    borderType=cv2.BORDER_CONSTANT,
                    value=(0,),
                )
            n_imgs.append(img_p)

        data["image"] = n_imgs
        return data