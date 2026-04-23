def lookup_remote_cache_entry(
    remote_cache: RemoteCache[JsonDataTy],
    cache_key: str,
    event_name: str | None = None,
) -> defaultdict[CodeId, CodeState] | None:
    code_state = None
    try:
        cache_data = remote_cache.get(cache_key)
    except Exception:
        log.warning("get_code_state failed remote read on %s", cache_key, exc_info=True)
    else:
        if cache_data is not None:
            try:
                assert isinstance(cache_data, dict)
                data = cache_data["data"]
                assert isinstance(data, str)
                payload = base64.b64decode(data)
                if event_name is not None:
                    CompileEventLogger.pt2_compile(
                        event_name, cache_size_bytes=len(payload)
                    )
                code_state = pickle.loads(payload)
            except Exception:
                log.warning(
                    "get_code_state failed parsing remote result on %s",
                    cache_key,
                    exc_info=True,
                )
            else:
                CacheArtifactManager.record_artifact(
                    PGOCacheArtifact.type(), cache_key, payload
                )
        else:
            log.info("get_code_state remote miss on %s", cache_key)
    return code_state