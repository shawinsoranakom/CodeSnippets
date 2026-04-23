def box_label(self, box, label: str = "", color: tuple = (128, 128, 128), txt_color: tuple = (255, 255, 255)):
        """Draw a bounding box on an image with a given label.

        Args:
            box (tuple): The bounding box coordinates (x1, y1, x2, y2).
            label (str, optional): The text label to be displayed.
            color (tuple, optional): The background color of the rectangle.
            txt_color (tuple, optional): The color of the text.

        Examples:
            >>> from ultralytics.utils.plotting import Annotator
            >>> im0 = cv2.imread("test.png")
            >>> annotator = Annotator(im0, line_width=10)
            >>> annotator.box_label(box=[10, 20, 30, 40], label="person")
        """
        txt_color = self.get_txt_color(color, txt_color)
        if isinstance(box, torch.Tensor):
            box = box.tolist()

        multi_points = isinstance(box[0], list)  # multiple points with shape (n, 2)
        p1 = [int(b) for b in box[0]] if multi_points else (int(box[0]), int(box[1]))
        if self.pil:
            self.draw.polygon(
                [tuple(b) for b in box], width=self.lw, outline=color
            ) if multi_points else self.draw.rectangle(box, width=self.lw, outline=color)
            if label:
                w, h = self.font.getsize(label)  # text width, height
                outside = p1[1] >= h  # label fits outside box
                if p1[0] > self.im.size[0] - w:  # size is (w, h), check if label extend beyond right side of image
                    p1 = self.im.size[0] - w, p1[1]
                self.draw.rectangle(
                    (p1[0], p1[1] - h if outside else p1[1], p1[0] + w + 1, p1[1] + 1 if outside else p1[1] + h + 1),
                    fill=color,
                )
                # self.draw.text([box[0], box[1]], label, fill=txt_color, font=self.font, anchor='ls')  # for PIL>8.0
                self.draw.text((p1[0], p1[1] - h if outside else p1[1]), label, fill=txt_color, font=self.font)
        else:  # cv2
            cv2.polylines(
                self.im, [np.asarray(box, dtype=int)], True, color, self.lw
            ) if multi_points else cv2.rectangle(
                self.im, p1, (int(box[2]), int(box[3])), color, thickness=self.lw, lineType=cv2.LINE_AA
            )
            if label:
                w, h = cv2.getTextSize(label, 0, fontScale=self.sf, thickness=self.tf)[0]  # text width, height
                h += 3  # add pixels to pad text
                outside = p1[1] >= h  # label fits outside box
                if p1[0] > self.im.shape[1] - w:  # shape is (h, w), check if label extend beyond right side of image
                    p1 = self.im.shape[1] - w, p1[1]
                p2 = p1[0] + w, p1[1] - h if outside else p1[1] + h
                cv2.rectangle(self.im, p1, p2, color, -1, cv2.LINE_AA)  # filled
                cv2.putText(
                    self.im,
                    label,
                    (p1[0], p1[1] - 2 if outside else p1[1] + h - 1),
                    0,
                    self.sf,
                    txt_color,
                    thickness=self.tf,
                    lineType=cv2.LINE_AA,
                )