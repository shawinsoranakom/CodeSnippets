def check_for_existance(file_list: list = None, is_train=False, is_dataset_processing=False):
    files_status = []
    if is_train == True and file_list:
        file_list.append(os.path.join(file_list[0], "2-name2text.txt"))
        file_list.append(os.path.join(file_list[0], "3-bert"))
        file_list.append(os.path.join(file_list[0], "4-cnhubert"))
        file_list.append(os.path.join(file_list[0], "5-wav32k"))
        file_list.append(os.path.join(file_list[0], "6-name2semantic.tsv"))
    for file in file_list:
        if os.path.exists(file):
            files_status.append(True)
        else:
            files_status.append(False)
    if sum(files_status) != len(files_status):
        if is_train:
            for file, status in zip(file_list, files_status):
                if status:
                    pass
                else:
                    gr.Warning(file)
            gr.Warning(i18n("以下文件或文件夹不存在"))
            return False
        elif is_dataset_processing:
            if files_status[0]:
                return True
            elif not files_status[0]:
                gr.Warning(file_list[0])
            elif not files_status[1] and file_list[1]:
                gr.Warning(file_list[1])
            gr.Warning(i18n("以下文件或文件夹不存在"))
            return False
        else:
            if file_list[0]:
                gr.Warning(file_list[0])
                gr.Warning(i18n("以下文件或文件夹不存在"))
            else:
                gr.Warning(i18n("路径不能为空"))
            return False
    return True