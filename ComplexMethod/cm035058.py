def projection(self, erosion, h, w, spilt_threshold=0):
        # 水平投影
        projection_map = np.ones_like(erosion)
        project_val_array = [0 for _ in range(0, h)]

        for j in range(0, h):
            for i in range(0, w):
                if erosion[j, i] == 255:
                    project_val_array[j] += 1
        # 根据数组，获取切割点
        start_idx = 0  # 记录进入字符区的索引
        end_idx = 0  # 记录进入空白区域的索引
        in_text = False  # 是否遍历到了字符区内
        box_list = []
        for i in range(len(project_val_array)):
            if (
                in_text == False and project_val_array[i] > spilt_threshold
            ):  # 进入字符区了
                in_text = True
                start_idx = i
            elif (
                project_val_array[i] <= spilt_threshold and in_text == True
            ):  # 进入空白区了
                end_idx = i
                in_text = False
                if end_idx - start_idx <= 2:
                    continue
                box_list.append((start_idx, end_idx + 1))

        if in_text:
            box_list.append((start_idx, h - 1))
        # 绘制投影直方图
        for j in range(0, h):
            for i in range(0, project_val_array[j]):
                projection_map[j, i] = 0
        return box_list, projection_map