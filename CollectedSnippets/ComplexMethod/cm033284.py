def get_files(files: Union[None, list[dict]], raw: bool = False, layout_recognize: str = None) -> Union[list[str], tuple[list[str], list[dict]]]:
        if not files:
            return  []
        def image_to_base64(file):
            return "data:{};base64,{}".format(file["mime_type"],
                                        base64.b64encode(FileService.get_blob(file["created_by"], file["id"])).decode("utf-8"))
        exe = ThreadPoolExecutor(max_workers=5)
        threads = []
        imgs = []
        for file in files:
            if file["mime_type"].find("image") >=0:
                if raw:
                    imgs.append(FileService.get_blob(file["created_by"], file["id"]))
                else:
                    threads.append(exe.submit(image_to_base64, file))
                continue
            threads.append(exe.submit(FileService.parse, file["name"], FileService.get_blob(file["created_by"], file["id"]), True, file["created_by"], layout_recognize))

        if raw:
            return [th.result() for th in threads], imgs
        else:
            return [th.result() for th in threads]