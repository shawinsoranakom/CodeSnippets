def _verify_nearliness(self, mask: torch.Tensor, nearliness: int):
        if nearliness <= 0:
            if not torch.all(mask == torch.zeros(mask.shape[0], mask.shape[1])):
                raise AssertionError(
                    "Expected all mask values to be 0 for nearliness <= 0"
                )
        else:
            height, width = mask.shape
            dist_to_diagonal = nearliness // 2
            for row in range(height):
                for col in range(width):
                    if abs(row - col) <= dist_to_diagonal:
                        if mask[row, col] != 1:
                            raise AssertionError(
                                f"Expected mask[{row}, {col}] == 1 for near-diagonal"
                            )
                    else:
                        if mask[row, col] != 0:
                            raise AssertionError(
                                f"Expected mask[{row}, {col}] == 0 for off-diagonal"
                            )