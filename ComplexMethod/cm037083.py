def _get_best_grid(img, side):
            img_area = img.size[0] * img.size[1]

            candidate_grids = []
            for i in range(1, max_partition + 1):
                for j in range(1, max_partition + 1):
                    if i * j <= max_partition:
                        candidate_grids.append((i, j))

            all_grids = []
            good_grids = []
            for grid in candidate_grids:
                partition = _partition(img, grid)
                covering_ratio = (
                    sum([_covering_area(*p, side) for p in partition]) / img_area
                )
                assert covering_ratio <= 1.0
                all_grids.append((grid, covering_ratio))
                if covering_ratio > covering_threshold:
                    good_grids.append((grid, covering_ratio))

            if len(good_grids) > 0:
                # pick the good partition with minimum #sub_images and break the tie using covering_ratio
                return sorted(good_grids, key=lambda x: (x[0][0] * x[0][1], -x[1]))[0][
                    0
                ]
            else:
                # pick the partition with maximum covering_ratio and break the tie using #sub_images
                return sorted(all_grids, key=lambda x: (-x[1], x[0][0] * x[0][1]))[0][0]