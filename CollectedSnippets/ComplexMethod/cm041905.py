def user_swipe(self, x: int, y: int, orient: str = "up", dist: str = "medium", if_quick: bool = False) -> str:
        dist_unit = int(self.width / 10)
        if dist == "long":
            dist_unit *= 3
        elif dist == "medium":
            dist_unit *= 2

        if orient == "up":
            offset = 0, -2 * dist_unit
        elif orient == "down":
            offset = 0, 2 * dist_unit
        elif orient == "left":
            offset = -1 * dist_unit, 0
        elif orient == "right":
            offset = dist_unit, 0
        else:
            return ADB_EXEC_FAIL

        duration = 100 if if_quick else 400
        adb_cmd = f"{self.adb_prefix_si} swipe {x} {y} {x + offset[0]} {y + offset[1]} {duration}"
        swipe_res = self.execute_adb_with_cmd(adb_cmd)
        return swipe_res