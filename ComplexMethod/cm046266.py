def display_counts(self, plot_im) -> None:
        """Display object counts on the input image or frame.

        Args:
            plot_im (np.ndarray): The image or frame to display counts on.

        Examples:
            >>> counter = ObjectCounter()
            >>> frame = cv2.imread("image.jpg")
            >>> counter.display_counts(frame)
        """
        labels_dict = {
            str.capitalize(key): f"{'IN ' + str(value['IN']) if self.show_in else ''} "
            f"{'OUT ' + str(value['OUT']) if self.show_out else ''}".strip()
            for key, value in self.classwise_count.items()
            if (value["IN"] != 0 and self.show_in) or (value["OUT"] != 0 and self.show_out)
        }
        if labels_dict:
            self.annotator.display_analytics(plot_im, labels_dict, (104, 31, 17), (255, 255, 255), self.margin)