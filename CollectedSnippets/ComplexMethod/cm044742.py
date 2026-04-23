def open1abc(
    version,
    inp_text,
    inp_wav_dir,
    exp_name,
    gpu_numbers1a,
    gpu_numbers1Ba,
    gpu_numbers1c,
    bert_pretrained_dir,
    ssl_pretrained_dir,
    pretrained_s2G_path,
):
    global ps1abc
    inp_text = my_utils.clean_path(inp_text)
    inp_wav_dir = my_utils.clean_path(inp_wav_dir)
    if check_for_existance([inp_text, inp_wav_dir], is_dataset_processing=True):
        check_details([inp_text, inp_wav_dir], is_dataset_processing=True)
    exp_name = exp_name.rstrip(" ")
    if ps1abc == []:
        opt_dir = "%s/%s" % (exp_root, exp_name)
        try:
            #############################1a
            path_text = "%s/2-name2text.txt" % opt_dir
            if os.path.exists(path_text) == False or (
                os.path.exists(path_text) == True
                and len(open(path_text, "r", encoding="utf8").read().strip("\n").split("\n")) < 2
            ):
                config = {
                    "inp_text": inp_text,
                    "inp_wav_dir": inp_wav_dir,
                    "exp_name": exp_name,
                    "opt_dir": opt_dir,
                    "bert_pretrained_dir": bert_pretrained_dir,
                    "is_half": str(is_half),
                }
                gpu_names = gpu_numbers1a.split("-")
                all_parts = len(gpu_names)
                for i_part in range(all_parts):
                    config.update(
                        {
                            "i_part": str(i_part),
                            "all_parts": str(all_parts),
                            "_CUDA_VISIBLE_DEVICES": str(fix_gpu_number(gpu_names[i_part])),
                        }
                    )
                    os.environ.update(config)
                    cmd = '"%s" -s GPT_SoVITS/prepare_datasets/1-get-text.py' % python_exec
                    print(cmd)
                    p = Popen(cmd, shell=True)
                    ps1abc.append(p)
                yield (
                    i18n("进度") + ": 1A-Doing",
                    {"__type__": "update", "visible": False},
                    {"__type__": "update", "visible": True},
                )
                for p in ps1abc:
                    p.wait()

                opt = []
                for i_part in range(all_parts):  # txt_path="%s/2-name2text-%s.txt"%(opt_dir,i_part)
                    txt_path = "%s/2-name2text-%s.txt" % (opt_dir, i_part)
                    with open(txt_path, "r", encoding="utf8") as f:
                        opt += f.read().strip("\n").split("\n")
                    os.remove(txt_path)
                with open(path_text, "w", encoding="utf8") as f:
                    f.write("\n".join(opt) + "\n")
                assert len("".join(opt)) > 0, process_info(process_name_1a, "failed")
            yield (
                i18n("进度") + ": 1A-Done",
                {"__type__": "update", "visible": False},
                {"__type__": "update", "visible": True},
            )
            ps1abc = []
            #############################1b
            config = {
                "inp_text": inp_text,
                "inp_wav_dir": inp_wav_dir,
                "exp_name": exp_name,
                "opt_dir": opt_dir,
                "cnhubert_base_dir": ssl_pretrained_dir,
                "sv_path": sv_path,
            }
            gpu_names = gpu_numbers1Ba.split("-")
            all_parts = len(gpu_names)
            for i_part in range(all_parts):
                config.update(
                    {
                        "i_part": str(i_part),
                        "all_parts": str(all_parts),
                        "_CUDA_VISIBLE_DEVICES": str(fix_gpu_number(gpu_names[i_part])),
                    }
                )
                os.environ.update(config)
                cmd = '"%s" -s GPT_SoVITS/prepare_datasets/2-get-hubert-wav32k.py' % python_exec
                print(cmd)
                p = Popen(cmd, shell=True)
                ps1abc.append(p)
            yield (
                i18n("进度") + ": 1A-Done, 1B-Doing",
                {"__type__": "update", "visible": False},
                {"__type__": "update", "visible": True},
            )
            for p in ps1abc:
                p.wait()
            ps1abc = []
            if "Pro" in version:
                for i_part in range(all_parts):
                    config.update(
                        {
                            "i_part": str(i_part),
                            "all_parts": str(all_parts),
                            "_CUDA_VISIBLE_DEVICES": str(fix_gpu_number(gpu_names[i_part])),
                        }
                    )
                    os.environ.update(config)
                    cmd = '"%s" -s GPT_SoVITS/prepare_datasets/2-get-sv.py' % python_exec
                    print(cmd)
                    p = Popen(cmd, shell=True)
                    ps1abc.append(p)
                for p in ps1abc:
                    p.wait()
                ps1abc = []
            yield (
                i18n("进度") + ": 1A-Done, 1B-Done",
                {"__type__": "update", "visible": False},
                {"__type__": "update", "visible": True},
            )
            #############################1c
            path_semantic = "%s/6-name2semantic.tsv" % opt_dir
            if os.path.exists(path_semantic) == False or (
                os.path.exists(path_semantic) == True and os.path.getsize(path_semantic) < 31
            ):
                config_file = (
                    "GPT_SoVITS/configs/s2.json"
                    if version not in {"v2Pro", "v2ProPlus"}
                    else f"GPT_SoVITS/configs/s2{version}.json"
                )
                config = {
                    "inp_text": inp_text,
                    "exp_name": exp_name,
                    "opt_dir": opt_dir,
                    "pretrained_s2G": pretrained_s2G_path,
                    "s2config_path": config_file,
                }
                gpu_names = gpu_numbers1c.split("-")
                all_parts = len(gpu_names)
                for i_part in range(all_parts):
                    config.update(
                        {
                            "i_part": str(i_part),
                            "all_parts": str(all_parts),
                            "_CUDA_VISIBLE_DEVICES": str(fix_gpu_number(gpu_names[i_part])),
                        }
                    )
                    os.environ.update(config)
                    cmd = '"%s" -s GPT_SoVITS/prepare_datasets/3-get-semantic.py' % python_exec
                    print(cmd)
                    p = Popen(cmd, shell=True)
                    ps1abc.append(p)
                yield (
                    i18n("进度") + ": 1A-Done, 1B-Done, 1C-Doing",
                    {"__type__": "update", "visible": False},
                    {"__type__": "update", "visible": True},
                )
                for p in ps1abc:
                    p.wait()

                opt = ["item_name\tsemantic_audio"]
                for i_part in range(all_parts):
                    semantic_path = "%s/6-name2semantic-%s.tsv" % (opt_dir, i_part)
                    with open(semantic_path, "r", encoding="utf8") as f:
                        opt += f.read().strip("\n").split("\n")
                    os.remove(semantic_path)
                with open(path_semantic, "w", encoding="utf8") as f:
                    f.write("\n".join(opt) + "\n")
                yield (
                    i18n("进度") + ": 1A-Done, 1B-Done, 1C-Done",
                    {"__type__": "update", "visible": False},
                    {"__type__": "update", "visible": True},
                )
            ps1abc = []
            yield (
                process_info(process_name_1abc, "finish"),
                {"__type__": "update", "visible": True},
                {"__type__": "update", "visible": False},
            )
        except:
            traceback.print_exc()
            close1abc()
            yield (
                process_info(process_name_1abc, "failed"),
                {"__type__": "update", "visible": True},
                {"__type__": "update", "visible": False},
            )
    else:
        yield (
            process_info(process_name_1abc, "occupy"),
            {"__type__": "update", "visible": False},
            {"__type__": "update", "visible": True},
        )