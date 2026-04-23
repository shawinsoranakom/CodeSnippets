def __call__(self, data):
        image = data["image"]

        h, w = image.shape[0:2]
        th, tw = self.size
        if w == tw and h == th:
            return data

        mask = data[self.main_key]
        if np.max(mask) > 0 and random.random() > self.p:
            # make sure to crop the text region
            tl = np.min(np.where(mask > 0), axis=1) - (th, tw)
            tl[tl < 0] = 0
            br = np.max(np.where(mask > 0), axis=1) - (th, tw)
            br[br < 0] = 0

            br[0] = min(br[0], h - th)
            br[1] = min(br[1], w - tw)

            i = random.randint(tl[0], br[0]) if tl[0] < br[0] else 0
            j = random.randint(tl[1], br[1]) if tl[1] < br[1] else 0
        else:
            i = random.randint(0, h - th) if h - th > 0 else 0
            j = random.randint(0, w - tw) if w - tw > 0 else 0

        # return i, j, th, tw
        for k in data:
            if k in self.crop_keys:
                if len(data[k].shape) == 3:
                    if np.argmin(data[k].shape) == 0:
                        img = data[k][:, i : i + th, j : j + tw]
                        if img.shape[1] != img.shape[2]:
                            a = 1
                    elif np.argmin(data[k].shape) == 2:
                        img = data[k][i : i + th, j : j + tw, :]
                        if img.shape[1] != img.shape[0]:
                            a = 1
                    else:
                        img = data[k]
                else:
                    img = data[k][i : i + th, j : j + tw]
                    if img.shape[0] != img.shape[1]:
                        a = 1
                data[k] = img
        return data