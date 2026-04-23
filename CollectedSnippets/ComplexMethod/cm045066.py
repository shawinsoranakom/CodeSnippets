async def call_tool(self, name: str, arguments: Optional[Dict[str, Any]] = None) -> list[TextContent]:
        """Call a specific tool."""
        if not arguments:
            arguments = {}

        if name == "echo":
            text = arguments.get("text", "")
            return [
                TextContent(
                    type="text",
                    text=f"Echo: {text}",
                )
            ]

        elif name == "get_time":
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return [
                TextContent(
                    type="text",
                    text=f"Current time: {current_time}",
                )
            ]

        elif name == "order_dish":
            dish = arguments.get("dish", "")

            class Order(BaseModel):
                dish: Literal["pizza", "pasta", "burger", "sushi", "tacos"]
                quantity: int = 1

            result = await self.server.request_context.session.elicit(
                f"{dish} is sold out. Please pick another option.",
                requestedSchema=Order.model_json_schema(),
            )

            if result.action == "accept":
                order = Order.model_validate(result.content)

                return [TextContent(type="text", text=f"You ordered {order.quantity} {order.dish}")]
            elif result.action == "decline":
                return [TextContent(type="text", text="You declined to change your order.")]
            else:
                return [TextContent(type="text", text="You cancelled request.")]

        elif name == "generate_poem":
            topic = arguments.get("topic", "")

            prompt = f"Write a short poem about {topic}"

            message_result = await self.server.request_context.session.create_message(
                messages=[
                    SamplingMessage(
                        role="user",
                        content=TextContent(type="text", text=prompt),
                    )
                ],
                max_tokens=100,
                temperature=0.6,
                stop_sequences=["\n\n"],
                system_prompt="You are a createive poet.",
            )

            if (
                message_result.content
                and hasattr(message_result.content, "type")
                and message_result.content.type == "text"
            ):
                return [TextContent(type="text", text=message_result.content.text)]
            return [TextContent(type="text", text=str(message_result.content))]

        elif name == "ls":
            path = arguments.get("path", "")

            roots = await self.server.request_context.session.list_roots()

            target_path = Path(path).resolve()

            is_allowed = False
            for root in roots.roots:
                if root.uri.path is None:
                    continue
                root_path = Path(root.uri.path).resolve()
                try:
                    target_path.relative_to(root_path)
                    is_allowed = True
                    break
                except ValueError:
                    continue

            if not is_allowed:
                return [TextContent(type="text", text=f"Error: Permission denied accessing '{path}'.")]

            simulated_files = [
                "config/",
                "data/",
                "logs/",
                "README.md",
                "app.py",
                "requirements.txt",
            ]

            return [TextContent(type="text", text="\n".join(simulated_files))]

        else:
            raise ValueError(f"Unknown tool: {name}")