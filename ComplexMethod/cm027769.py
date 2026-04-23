def create_mobject_matrix(
        self,
        matrix: GenericMatrixType,
        v_buff: float,
        h_buff: float,
        aligned_corner: Vect3,
        **element_config
    ) -> VMobjectMatrixType:
        """
        Creates and organizes the matrix of mobjects
        """
        mob_matrix = [
            [
                self.element_to_mobject(element, **element_config)
                for element in row
            ]
            for row in matrix
        ]
        max_width = max(elem.get_width() for row in mob_matrix for elem in row)
        max_height = max(elem.get_height() for row in mob_matrix for elem in row)
        x_step = (max_width + h_buff) * RIGHT
        y_step = (max_height + v_buff) * DOWN
        for i, row in enumerate(mob_matrix):
            for j, elem in enumerate(row):
                elem.move_to(i * y_step + j * x_step, aligned_corner)
        return mob_matrix