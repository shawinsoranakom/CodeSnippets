def __call__(
        self,
        img_path: Union[str, Path],
        table_results,
        save_html_path: Optional[Union[str, Path]] = None,
        save_drawed_path: Optional[Union[str, Path]] = None,
        save_logic_path: Optional[Union[str, Path]] = None,
    ):
        if save_html_path:
            html_with_border = self.insert_border_style(table_results.pred_html)
            self.save_html(save_html_path, html_with_border)

        table_cell_bboxes = table_results.cell_bboxes
        table_logic_points = table_results.logic_points
        if table_cell_bboxes is None:
            return None

        img = self.load_img(img_path)

        dims_bboxes = table_cell_bboxes.shape[1]
        if dims_bboxes == 4:
            drawed_img = self.draw_rectangle(img, table_cell_bboxes)
        elif dims_bboxes == 8:
            drawed_img = self.draw_polylines(img, table_cell_bboxes)
        else:
            raise ValueError("Shape of table bounding boxes is not between in 4 or 8.")

        if save_drawed_path:
            self.save_img(save_drawed_path, drawed_img)

        if save_logic_path:
            polygons = [[box[0], box[1], box[4], box[5]] for box in table_cell_bboxes]
            self.plot_rec_box_with_logic_info(
                img, save_logic_path, table_logic_points, polygons
            )
        return drawed_img