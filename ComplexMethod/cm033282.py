def upload_document(self, kb, file_objs, user_id, src="local", parent_path: str | None = None):
        root_folder = self.get_root_folder(user_id)
        pf_id = root_folder["id"]
        self.init_knowledgebase_docs(pf_id, user_id)
        kb_root_folder = self.get_kb_folder(user_id)
        kb_folder = self.new_a_file_from_kb(kb.tenant_id, kb.name, kb_root_folder["id"])

        safe_parent_path = sanitize_path(parent_path)

        err, files = [], []
        for file in file_objs:
            doc_id = file.id if hasattr(file, "id") else get_uuid()
            e, doc = DocumentService.get_by_id(doc_id)
            if e:
                try:
                    if str(doc.kb_id) != str(kb.id):
                        logging.warning(
                            "Existing document id collision detected for %s: belongs to kb_id=%s, incoming kb_id=%s. "
                            "Skipping update to avoid cross-KB overwrite.",
                            doc_id,
                            doc.kb_id,
                            kb.id,
                        )
                        user_msg = "Existing document id collision with another knowledge base; skipping update."
                        err.append(file.filename + ": " + user_msg)
                        continue
                    blob = file.read()
                    new_hash = xxhash.xxh128(blob).hexdigest()
                    old_hash = doc.content_hash or ""
                    settings.STORAGE_IMPL.put(kb.id, doc.location, blob, kb.tenant_id)
                    doc.size = len(blob)
                    doc.content_hash = new_hash
                    doc = doc.to_dict()
                    DocumentService.update_by_id(doc["id"], doc)
                    if new_hash != old_hash:
                        files.append((doc, blob))
                except Exception as exc:
                    logging.exception(f"Failed to update document {doc_id}: {exc}")
                    err.append(file.filename + ": " + str(exc))
                continue
            try:
                DocumentService.check_doc_health(kb.tenant_id, file.filename)
                filename = duplicate_name(DocumentService.query, name=file.filename, kb_id=kb.id)
                filetype = filename_type(filename)
                if filetype == FileType.OTHER.value:
                    raise RuntimeError("This type of file has not been supported yet!")

                location = filename if not safe_parent_path else f"{safe_parent_path}/{filename}"
                while settings.STORAGE_IMPL.obj_exist(kb.id, location):
                    location += "_"

                blob = file.read()
                if filetype == FileType.PDF.value:
                    blob = read_potential_broken_pdf(blob)
                settings.STORAGE_IMPL.put(kb.id, location, blob)


                img = thumbnail_img(filename, blob)
                thumbnail_location = ""
                if img is not None:
                    thumbnail_location = f"thumbnail_{doc_id}.png"
                    settings.STORAGE_IMPL.put(kb.id, thumbnail_location, img)

                doc = {
                    "id": doc_id,
                    "kb_id": kb.id,
                    "parser_id": self.get_parser(filetype, filename, kb.parser_id),
                    "pipeline_id": kb.pipeline_id,
                    "parser_config": kb.parser_config,
                    "created_by": user_id,
                    "type": filetype,
                    "name": filename,
                    "source_type": src,
                    "suffix": Path(filename).suffix.lstrip("."),
                    "location": location,
                    "size": len(blob),
                    "thumbnail": thumbnail_location,
                    "content_hash": xxhash.xxh128(blob).hexdigest(),
                }
                DocumentService.insert(doc)

                FileService.add_file_from_kb(doc, kb_folder["id"], kb.tenant_id)
                files.append((doc, blob))
            except Exception as e:
                err.append(file.filename + ": " + str(e))

        return err, files