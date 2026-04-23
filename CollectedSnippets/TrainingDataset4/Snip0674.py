def process(self):
    for i in range(self.dst_h):
        for j in range(self.dst_w):
            self.output[i][j] = self.img[self.get_y(i)][self.get_x(j)]
