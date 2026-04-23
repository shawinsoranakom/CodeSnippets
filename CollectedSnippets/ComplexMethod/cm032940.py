def init_settings():
    global DATABASE_TYPE, DATABASE
    DATABASE_TYPE = os.getenv("DB_TYPE", "mysql")
    DATABASE = decrypt_database_config(name=DATABASE_TYPE)

    global ALLOWED_LLM_FACTORIES, LLM_FACTORY, LLM_BASE_URL
    llm_settings = get_base_config("user_default_llm", {}) or {}
    llm_default_models = llm_settings.get("default_models", {}) or {}
    LLM_FACTORY = llm_settings.get("factory", "") or ""
    LLM_BASE_URL = llm_settings.get("base_url", "") or ""
    ALLOWED_LLM_FACTORIES = llm_settings.get("allowed_factories", None)

    global REGISTER_ENABLED
    try:
        REGISTER_ENABLED = int(os.environ.get("REGISTER_ENABLED", "1"))
    except Exception:
        pass

    global DISABLE_PASSWORD_LOGIN
    try:
        env_val = os.environ.get("DISABLE_PASSWORD_LOGIN", "").lower()
        if env_val in ("1", "true", "yes"):
            DISABLE_PASSWORD_LOGIN = True
        else:
            authentication_conf = get_base_config("authentication", {})
            DISABLE_PASSWORD_LOGIN = bool(authentication_conf.get("disable_password_login", False))
    except Exception:
        pass

    global FACTORY_LLM_INFOS
    try:
        with open(os.path.join(get_project_base_directory(), "conf", "llm_factories.json"), "r") as f:
            FACTORY_LLM_INFOS = json.load(f)["factory_llm_infos"]
    except Exception:
        FACTORY_LLM_INFOS = []

    global API_KEY
    API_KEY = llm_settings.get("api_key")

    global PARSERS
    PARSERS = llm_settings.get(
        "parsers", "naive:General,qa:Q&A,resume:Resume,manual:Manual,table:Table,paper:Paper,book:Book,laws:Laws,presentation:Presentation,picture:Picture,one:One,audio:Audio,email:Email,tag:Tag"
    )

    global CHAT_MDL, EMBEDDING_MDL, RERANK_MDL, ASR_MDL, IMAGE2TEXT_MDL
    chat_entry = _parse_model_entry(llm_default_models.get("chat_model", CHAT_MDL))
    embedding_entry = _parse_model_entry(llm_default_models.get("embedding_model", EMBEDDING_MDL))
    rerank_entry = _parse_model_entry(llm_default_models.get("rerank_model", RERANK_MDL))
    asr_entry = _parse_model_entry(llm_default_models.get("asr_model", ASR_MDL))
    image2text_entry = _parse_model_entry(llm_default_models.get("image2text_model", IMAGE2TEXT_MDL))

    global CHAT_CFG, EMBEDDING_CFG, RERANK_CFG, ASR_CFG, IMAGE2TEXT_CFG
    CHAT_CFG = _resolve_per_model_config(chat_entry, LLM_FACTORY, API_KEY, LLM_BASE_URL)
    EMBEDDING_CFG = _resolve_per_model_config(embedding_entry, LLM_FACTORY, API_KEY, LLM_BASE_URL)
    RERANK_CFG = _resolve_per_model_config(rerank_entry, LLM_FACTORY, API_KEY, LLM_BASE_URL)
    ASR_CFG = _resolve_per_model_config(asr_entry, LLM_FACTORY, API_KEY, LLM_BASE_URL)
    IMAGE2TEXT_CFG = _resolve_per_model_config(image2text_entry, LLM_FACTORY, API_KEY, LLM_BASE_URL)

    CHAT_MDL = CHAT_CFG.get("model", "") or ""
    EMBEDDING_MDL = EMBEDDING_CFG.get("model", "") or ""
    compose_profiles = os.getenv("COMPOSE_PROFILES", "")
    if "tei-" in compose_profiles:
        EMBEDDING_MDL = os.getenv("TEI_MODEL", EMBEDDING_MDL or "BAAI/bge-small-en-v1.5")
    RERANK_MDL = RERANK_CFG.get("model", "") or ""
    ASR_MDL = ASR_CFG.get("model", "") or ""
    IMAGE2TEXT_MDL = IMAGE2TEXT_CFG.get("model", "") or ""

    global HOST_IP, HOST_PORT
    HOST_IP = get_base_config(RAG_FLOW_SERVICE_NAME, {}).get("host", "127.0.0.1")
    HOST_PORT = get_base_config(RAG_FLOW_SERVICE_NAME, {}).get("http_port")

    global SECRET_KEY
    SECRET_KEY = _get_or_create_secret_key()


    # authentication
    authentication_conf = get_base_config("authentication", {})

    global CLIENT_AUTHENTICATION, HTTP_APP_KEY, GITHUB_OAUTH, FEISHU_OAUTH, OAUTH_CONFIG
    # client
    CLIENT_AUTHENTICATION = authentication_conf.get("client", {}).get("switch", False)
    HTTP_APP_KEY = authentication_conf.get("client", {}).get("http_app_key")
    GITHUB_OAUTH = get_base_config("oauth", {}).get("github")
    FEISHU_OAUTH = get_base_config("oauth", {}).get("feishu")
    OAUTH_CONFIG = get_base_config("oauth", {})

    global DOC_ENGINE, DOC_ENGINE_INFINITY, DOC_ENGINE_OCEANBASE, docStoreConn, ES, OB, OS, INFINITY
    DOC_ENGINE = os.environ.get("DOC_ENGINE", "elasticsearch").strip()
    DOC_ENGINE_INFINITY = (DOC_ENGINE.lower() == "infinity")
    DOC_ENGINE_OCEANBASE = (DOC_ENGINE.lower() == "oceanbase")
    lower_case_doc_engine = DOC_ENGINE.lower()
    if lower_case_doc_engine == "elasticsearch":
        ES = get_base_config("es", {})
        docStoreConn = rag.utils.es_conn.ESConnection()
    elif lower_case_doc_engine == "infinity":
        INFINITY = get_base_config("infinity", {
            "uri": "infinity:23817",
            "postgres_port": 5432,
            "db_name": "default_db"
        })
        docStoreConn = rag.utils.infinity_conn.InfinityConnection()
    elif lower_case_doc_engine == "opensearch":
        OS = get_base_config("os", {})
        docStoreConn = rag.utils.opensearch_conn.OSConnection()
    elif lower_case_doc_engine == "oceanbase":
        OB = get_base_config("oceanbase", {})
        docStoreConn = rag.utils.ob_conn.OBConnection()
    elif lower_case_doc_engine == "seekdb":
        OB = get_base_config("seekdb", {})
        docStoreConn = rag.utils.ob_conn.OBConnection()
    else:
        raise Exception(f"Not supported doc engine: {DOC_ENGINE}")

    global msgStoreConn
    # use the same engine for message store
    if DOC_ENGINE == "elasticsearch":
        ES = get_base_config("es", {})
        msgStoreConn = memory_es_conn.ESConnection()
    elif DOC_ENGINE == "infinity":
        INFINITY = get_base_config("infinity", {
            "uri": "infinity:23817",
            "postgres_port": 5432,
            "db_name": "default_db"
        })
        msgStoreConn = memory_infinity_conn.InfinityConnection()
    elif lower_case_doc_engine in ["oceanbase", "seekdb"]:
        msgStoreConn = memory_ob_conn.OBConnection()

    global AZURE, S3, MINIO, OSS, GCS
    if STORAGE_IMPL_TYPE in ['AZURE_SPN', 'AZURE_SAS']:
        AZURE = get_base_config("azure", {})
    elif STORAGE_IMPL_TYPE == 'AWS_S3':
        S3 = get_base_config("s3", {})
    elif STORAGE_IMPL_TYPE == 'MINIO':
        MINIO = decrypt_database_config(name="minio")
    elif STORAGE_IMPL_TYPE == 'OSS':
        OSS = get_base_config("oss", {})
    elif STORAGE_IMPL_TYPE == 'GCS':
        GCS = get_base_config("gcs", {})

    global STORAGE_IMPL
    storage_impl = StorageFactory.create(Storage[STORAGE_IMPL_TYPE])

    # Define crypto settings
    crypto_enabled = os.environ.get("RAGFLOW_CRYPTO_ENABLED", "false").lower() == "true"

    # Check if encryption is enabled
    if crypto_enabled:
        try:
            from rag.utils.encrypted_storage import create_encrypted_storage
            algorithm = os.environ.get("RAGFLOW_CRYPTO_ALGORITHM", "aes-256-cbc")
            crypto_key = os.environ.get("RAGFLOW_CRYPTO_KEY")

            STORAGE_IMPL = create_encrypted_storage(storage_impl, 
                algorithm=algorithm, 
                key=crypto_key, 
                encryption_enabled=crypto_enabled)
        except Exception as e:
            logging.error(f"Failed to initialize encrypted storage: {e}")
            STORAGE_IMPL = storage_impl
    else:
        STORAGE_IMPL = storage_impl

    global retriever, kg_retriever
    retriever = search.Dealer(docStoreConn)
    from rag.graphrag import search as kg_search

    kg_retriever = kg_search.KGSearch(docStoreConn)

    global SANDBOX_HOST
    if int(os.environ.get("SANDBOX_ENABLED", "0")):
        SANDBOX_HOST = os.environ.get("SANDBOX_HOST", "sandbox-executor-manager")

    global SMTP_CONF
    SMTP_CONF = get_base_config("smtp", {})

    global MAIL_SERVER, MAIL_PORT, MAIL_USE_SSL, MAIL_USE_TLS, MAIL_USERNAME, MAIL_PASSWORD, MAIL_DEFAULT_SENDER, MAIL_FRONTEND_URL
    MAIL_SERVER = SMTP_CONF.get("mail_server", "")
    MAIL_PORT = SMTP_CONF.get("mail_port", 000)
    MAIL_USE_SSL = SMTP_CONF.get("mail_use_ssl", True)
    MAIL_USE_TLS = SMTP_CONF.get("mail_use_tls", False)
    MAIL_USERNAME = SMTP_CONF.get("mail_username", "")
    MAIL_PASSWORD = SMTP_CONF.get("mail_password", "")
    mail_default_sender = SMTP_CONF.get("mail_default_sender", [])
    if mail_default_sender and len(mail_default_sender) >= 2:
        MAIL_DEFAULT_SENDER = (mail_default_sender[0], mail_default_sender[1])
    MAIL_FRONTEND_URL = SMTP_CONF.get("mail_frontend_url", "")

    global DOC_MAXIMUM_SIZE, DOC_BULK_SIZE, EMBEDDING_BATCH_SIZE
    DOC_MAXIMUM_SIZE = int(os.environ.get("MAX_CONTENT_LENGTH", 128 * 1024 * 1024))
    DOC_BULK_SIZE = int(os.environ.get("DOC_BULK_SIZE", 4))
    EMBEDDING_BATCH_SIZE = int(os.environ.get("EMBEDDING_BATCH_SIZE", 16))

    os.environ["DOTNET_SYSTEM_GLOBALIZATION_INVARIANT"] = "1"