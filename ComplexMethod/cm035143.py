async def _format_output(
        self,
        result: Dict,
        detailed: bool,
        ctx: Context,
        **kwargs: Any,
    ) -> Union[str, List[Union[TextContent, ImageContent]]]:
        if not result["markdown"].strip():
            return (
                "❌ No document content detected"
                if not detailed
                else json.dumps({"error": "No content detected"}, ensure_ascii=False)
            )

        markdown_text = result["markdown"]
        images_mapping = result.get("images_mapping", {})

        if kwargs.get("return_images"):
            content_list = self._parse_markdown_with_images(
                markdown_text, images_mapping
            )
        else:
            content_list = [TextContent(type="text", text=markdown_text)]

        if detailed:
            if "detailed_results" in result and result["detailed_results"]:
                for detailed_result in result["detailed_results"]:
                    content_list.append(
                        TextContent(
                            type="text",
                            text=json.dumps(
                                detailed_result,
                                ensure_ascii=False,
                                indent=2,
                                default=str,
                            ),
                        )
                    )

        return content_list