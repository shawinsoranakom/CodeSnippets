async def xml_fill(self, context: str, images: Optional[Union[str, list[str]]] = None) -> Dict[str, Any]:
        """
        Fill context with XML tags and convert according to field types, including string, integer, boolean, list and dict types
        """
        field_names = self.get_field_names()
        field_types = self.get_field_types()

        extracted_data: Dict[str, Any] = {}
        content = await self.llm.aask(context, images=images)

        for field_name in field_names:
            pattern = rf"<{field_name}>(.*?)</{field_name}>"
            match = re.search(pattern, content, re.DOTALL)
            if match:
                raw_value = match.group(1).strip()
                field_type = field_types.get(field_name)

                if field_type == str:
                    extracted_data[field_name] = raw_value
                elif field_type == int:
                    try:
                        extracted_data[field_name] = int(raw_value)
                    except ValueError:
                        extracted_data[field_name] = 0  # 或者其他默认值
                elif field_type == bool:
                    extracted_data[field_name] = raw_value.lower() in ("true", "yes", "1", "on", "True")
                elif field_type == list:
                    try:
                        extracted_data[field_name] = eval(raw_value)
                        if not isinstance(extracted_data[field_name], list):
                            raise ValueError
                    except:
                        extracted_data[field_name] = []  # 默认空列表
                elif field_type == dict:
                    try:
                        extracted_data[field_name] = eval(raw_value)
                        if not isinstance(extracted_data[field_name], dict):
                            raise ValueError
                    except:
                        extracted_data[field_name] = {}  # 默认空字典

        return extracted_data