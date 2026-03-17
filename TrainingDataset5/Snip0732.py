def stretch(self, input_image):
    self.img = cv2.imread(input_image, 0)
    self.original_image = copy.deepcopy(self.img)
    x, _, _ = plt.hist(self.img.ravel(), 256, [0, 256], label="x")
    self.k = np.sum(x)
    for i in range(len(x)):
        prk = x[i] / self.k
        self.sk += prk
        last = (self.L - 1) * self.sk
        if self.rem != 0:
            self.rem = int(last % last)
        last = int(last + 1 if self.rem >= 0.5 else last)
        self.last_list.append(last)
        self.number_of_rows = int(np.ma.count(self.img) / self.img[1].size)
        self.number_of_cols = self.img[1].size
    for i in range(self.number_of_cols):
        for j in range(self.number_of_rows):
            num = self.img[j][i]
            if num != self.last_list[num]:
                self.img[j][i] = self.last_list[num]
    cv2.imwrite("output_data/output.jpg", self.img)
