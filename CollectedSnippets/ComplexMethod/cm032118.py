def construct_vector_store(vs_id, vs_path, files, sentence_size, history, one_content, one_content_segmentation, text2vec):
    for file in files:
        assert os.path.exists(file), "输入文件不存在：" + file
    import nltk
    if NLTK_DATA_PATH not in nltk.data.path: nltk.data.path = [NLTK_DATA_PATH] + nltk.data.path
    local_doc_qa = LocalDocQA()
    local_doc_qa.init_cfg()
    filelist = []
    if not os.path.exists(os.path.join(vs_path, vs_id)):
        os.makedirs(os.path.join(vs_path, vs_id))
    for file in files:
        file_name = file.name if not isinstance(file, str) else file
        filename = os.path.split(file_name)[-1]
        shutil.copyfile(file_name, os.path.join(vs_path, vs_id, filename))
        filelist.append(os.path.join(vs_path, vs_id, filename))
    vs_path, loaded_files = local_doc_qa.init_knowledge_vector_store(filelist, os.path.join(vs_path, vs_id), sentence_size, text2vec)

    if len(loaded_files):
        file_status = f"已添加 {'、'.join([os.path.split(i)[-1] for i in loaded_files if i])} 内容至知识库，并已加载知识库，请开始提问"
    else:
        pass
        # file_status = "文件未成功加载，请重新上传文件"
    # logger.info(file_status)
    return local_doc_qa, vs_path