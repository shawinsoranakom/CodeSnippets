def fn(a, version):
            x = torch.tensor([1, 2], device=self.device, dtype=torch.int32)
            y = torch.tensor([2, 3], device=self.device, dtype=torch.int32)

            xx = torch.tensor([1, 2], device=self.device).view(1, 2)
            yy = torch.tensor([1, 2, 3], device=self.device).view(3, 1)

            if version == 0:
                a[x, y] = torch.zeros_like(a[x, y])
            elif version == 1:
                a[:, x, y] = torch.zeros_like(a[:, x, y])
            elif version == 2:
                a[:, x, y, :] = torch.zeros_like(a[:, x, y, :])
            elif version == 3:
                a[x, :, y] = torch.zeros_like(a[x, :, y])
            elif version == 4:
                a[:, x, :, y, :] = torch.zeros_like(a[:, x, :, y, :])
            elif version == 5:
                a[xx, yy] = torch.zeros_like(a[xx, yy])
            elif version == 6:
                a[:, xx, yy] = torch.zeros_like(a[:, xx, yy])
            elif version == 7:
                a[xx, :, yy] = torch.zeros_like(a[xx, :, yy])
            elif version == 8:
                a[xx, yy, :] = torch.zeros_like(a[xx, yy, :])
            elif version == 9:
                a[:, xx, :, yy] = torch.zeros_like(a[:, xx, :, yy])

            return a