def create_new_user(user_info: dict) -> dict:
    """
    Add a new user, and create tenant, tenant llm, file folder for new user.
    :param user_info: {
        "email": <example@example.com>,
        "nickname": <str, "name">,
        "password": <decrypted password>,
        "login_channel": <enum, "password">,
        "is_superuser": <bool, role == "admin">,
    }
    :return: {
        "success": <bool>,
        "user_info": <dict>, # if true, return user_info
    }
    """
    # generate user_id and access_token for user
    user_id = uuid.uuid1().hex
    user_info['id'] = user_id
    user_info['access_token'] = uuid.uuid1().hex
    # construct tenant info
    tenant = {
        "id": user_id,
        "name": user_info["nickname"] + "‘s Kingdom",
        "llm_id": settings.CHAT_MDL,
        "embd_id": settings.EMBEDDING_MDL,
        "asr_id": settings.ASR_MDL,
        "parser_ids": settings.PARSERS,
        "img2txt_id": settings.IMAGE2TEXT_MDL,
        "rerank_id": settings.RERANK_MDL,
    }
    usr_tenant = {
        "tenant_id": user_id,
        "user_id": user_id,
        "invited_by": user_id,
        "role": UserTenantRole.OWNER,
    }
    # construct file folder info
    file_id = uuid.uuid1().hex
    file = {
        "id": file_id,
        "parent_id": file_id,
        "tenant_id": user_id,
        "created_by": user_id,
        "name": "/",
        "type": FileType.FOLDER.value,
        "size": 0,
        "location": "",
    }
    try:
        tenant_llm = get_init_tenant_llm(user_id)

        if not UserService.save(**user_info):
            return {"success": False}

        TenantService.insert(**tenant)
        UserTenantService.insert(**usr_tenant)
        TenantLLMService.insert_many(tenant_llm)
        FileService.insert(file)

        return {
            "success": True,
            "user_info": user_info,
        }

    except Exception as create_error:
        logging.exception(create_error)
        # rollback
        try:
            metadata_index_name = DocMetadataService._get_doc_meta_index_name(user_id)
            settings.docStoreConn.delete_idx(metadata_index_name, "")
        except Exception as e:
            logging.exception(e)
        try:
            TenantService.delete_by_id(user_id)
        except Exception as e:
            logging.exception(e)
        try:
            u = UserTenantService.query(tenant_id=user_id)
            if u:
                UserTenantService.delete_by_id(u[0].id)
        except Exception as e:
            logging.exception(e)
        try:
            TenantLLMService.delete_by_tenant_id(user_id)
        except Exception as e:
            logging.exception(e)
        try:
            FileService.delete_by_id(file["id"])
        except Exception as e:
            logging.exception(e)
        # delete user row finally
        try:
            UserService.delete_by_id(user_id)
        except Exception as e:
            logging.exception(e)
        # reraise
        raise create_error