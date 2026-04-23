def save(key: str, entry: GenericAOTAutogradResult[Any, Any], remote: bool) -> None:
        """Save a single entry into the cache."""
        content: bytes | None = None
        try:
            entry.pre_save()
            content = AOTAutogradCache._pickle_entry(entry, remote)
            if content is None:
                return None
            CacheArtifactManager.record_artifact(
                AOTAutogradCacheArtifact.type(), key, content
            )
            if (
                should_bundle_autograd_cache()
                and entry.sanitized_aot_config.precompile_backend_id is not None
            ):
                precompile_key = entry.sanitized_aot_config.precompile_backend_id
                artifact = BundledAOTAutogradCacheArtifact(precompile_key, entry)
                entry.sanitized_aot_config.precompile_backend_id = None
                PrecompileContext.record_artifact(artifact)
            AOTAutogradCache._write_to_local_cache(key, content)
            counters["aot_autograd"]["autograd_cache_saved"] += 1
        except BypassAOTAutogradCache as e:
            AOTAutogradCache._handle_save_error(e, remote, is_bypass=True)
            return None
        except Exception as e:
            AOTAutogradCache._handle_save_error(e, remote, is_bypass=False)
            return None

        if remote:
            remote_cache = AOTAutogradCache.get_remote_cache()
            if remote_cache is not None:
                time_taken_ms = int(
                    (entry.forward_time_taken_ns + entry.backward_time_taken_ns) // 1e6
                )
                cache_data: JsonDataTy = {
                    "data": base64.b64encode(content).decode("ascii"),
                    "time_taken_ms": time_taken_ms,
                }
                remote_cache.put(key, cache_data)