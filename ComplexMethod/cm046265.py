def count_objects(
        self,
        current_centroid: tuple[float, float],
        track_id: int,
        prev_position: tuple[float, float] | None,
        cls: int,
    ) -> None:
        """Count objects within a polygonal or linear region based on their tracks.

        Args:
            current_centroid (tuple[float, float]): Current centroid coordinates (x, y) in the current frame.
            track_id (int): Unique identifier for the tracked object.
            prev_position (tuple[float, float], optional): Last frame position coordinates (x, y) of the track.
            cls (int): Class index for classwise count updates.

        Examples:
            >>> counter = ObjectCounter()
            >>> track_line = {1: [100, 200], 2: [110, 210], 3: [120, 220]}
            >>> box = [130, 230, 150, 250]
            >>> track_id_num = 1
            >>> previous_position = (120, 220)
            >>> class_to_count = 0  # In COCO model, class 0 = person
            >>> counter.count_objects((140, 240), track_id_num, previous_position, class_to_count)
        """
        if prev_position is None or track_id in self.counted_ids:
            return

        if len(self.region) == 2:  # Linear region (defined as a line segment)
            if self.r_s.intersects(self.LineString([prev_position, current_centroid])):
                # Determine orientation of the region (vertical or horizontal)
                if abs(self.region[0][0] - self.region[1][0]) < abs(self.region[0][1] - self.region[1][1]):
                    # Vertical region: Compare x-coordinates to determine direction
                    if current_centroid[0] > prev_position[0]:  # Moving right
                        self.in_count += 1
                        self.classwise_count[self.names[cls]]["IN"] += 1
                    else:  # Moving left
                        self.out_count += 1
                        self.classwise_count[self.names[cls]]["OUT"] += 1
                # Horizontal region: Compare y-coordinates to determine direction
                elif current_centroid[1] > prev_position[1]:  # Moving downward
                    self.in_count += 1
                    self.classwise_count[self.names[cls]]["IN"] += 1
                else:  # Moving upward
                    self.out_count += 1
                    self.classwise_count[self.names[cls]]["OUT"] += 1
                self.counted_ids.append(track_id)

        elif len(self.region) > 2:  # Polygonal region
            if self.r_s.contains(self.Point(current_centroid)):
                # Determine motion direction for vertical or horizontal polygons
                region_width = max(p[0] for p in self.region) - min(p[0] for p in self.region)
                region_height = max(p[1] for p in self.region) - min(p[1] for p in self.region)

                if (region_width < region_height and current_centroid[0] > prev_position[0]) or (
                    region_width >= region_height and current_centroid[1] > prev_position[1]
                ):  # Moving right or downward
                    self.in_count += 1
                    self.classwise_count[self.names[cls]]["IN"] += 1
                else:  # Moving left or upward
                    self.out_count += 1
                    self.classwise_count[self.names[cls]]["OUT"] += 1
                self.counted_ids.append(track_id)