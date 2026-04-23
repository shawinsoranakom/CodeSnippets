async def _omniparse_read_file(path: Union[str, Path], auto_save_image: bool = False) -> Optional[str]:
        from metagpt.tools.libs import get_env_default
        from metagpt.utils.omniparse_client import OmniParseClient

        env_base_url = await get_env_default(key="base_url", app_name="OmniParse", default_value="")
        env_timeout = await get_env_default(key="timeout", app_name="OmniParse", default_value="")
        conf_base_url, conf_timeout = await File._read_omniparse_config()

        base_url = env_base_url or conf_base_url
        if not base_url:
            return None
        api_key = await get_env_default(key="api_key", app_name="OmniParse", default_value="")
        timeout = env_timeout or conf_timeout or 600
        try:
            timeout = int(timeout)
        except ValueError:
            timeout = 600

        try:
            if not await check_http_endpoint(url=base_url):
                logger.warning(f"{base_url}: NOT AVAILABLE")
                return None
            client = OmniParseClient(api_key=api_key, base_url=base_url, max_timeout=timeout)
            file_data = await aread_bin(filename=path)
            ret = await client.parse_document(file_input=file_data, bytes_filename=str(path))
        except (ValueError, Exception) as e:
            logger.exception(f"{path}: {e}")
            return None
        if not ret.images or not auto_save_image:
            return ret.text

        result = [ret.text]
        img_dir = Path(path).parent / (Path(path).name.replace(".", "_") + "_images")
        img_dir.mkdir(parents=True, exist_ok=True)
        for i in ret.images:
            byte_data = base64.b64decode(i.image)
            filename = img_dir / i.image_name
            await awrite_bin(filename=filename, data=byte_data)
            result.append(f"![{i.image_name}]({str(filename)})")
        return "\n".join(result)