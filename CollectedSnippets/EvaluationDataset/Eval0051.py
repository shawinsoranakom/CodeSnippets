def update_image_and_anno(
    img_list: list, anno_list: list, flip_type: int = 1
) -> tuple[list, list, list]:
    new_annos_lists = []
    path_list = []
    new_imgs_list = []
    for idx in range(len(img_list)):
        new_annos = []
        path = img_list[idx]
        path_list.append(path)
        img_annos = anno_list[idx]
        img = cv2.imread(path)
        if flip_type == 1:
            new_img = cv2.flip(img, flip_type)
            for bbox in img_annos:
                x_center_new = 1 - bbox[1]
                new_annos.append([bbox[0], x_center_new, bbox[2], bbox[3], bbox[4]])
        elif flip_type == 0:
            new_img = cv2.flip(img, flip_type)
            for bbox in img_annos:
                y_center_new = 1 - bbox[2]
                new_annos.append([bbox[0], bbox[1], y_center_new, bbox[3], bbox[4]])
        new_annos_lists.append(new_annos)
        new_imgs_list.append(new_img)
    return new_imgs_list, new_annos_lists, path_list
