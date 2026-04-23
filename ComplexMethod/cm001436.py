async def todo_decompose(self, item_index: int, context: str = "") -> dict:
        """
        Use the smart LLM to break down a todo item into actionable sub-steps.

        This spawns a focused decomposition call with the current plan context.
        The LLM analyzes the task and generates 3-7 concrete sub-steps.

        Requires an LLM provider to be configured for this component.
        """
        # Validate LLM availability
        if not self._llm_provider or not self._smart_llm:
            return {
                "status": "error",
                "message": "LLM provider not configured. Cannot decompose tasks.",
            }

        # Validate item index
        max_idx = len(self._todos.items) - 1
        if item_index < 0 or item_index > max_idx:
            return {
                "status": "error",
                "message": f"Invalid item_index {item_index}. Valid: 0-{max_idx}",
            }

        target_item = self._todos.items[item_index]

        # Check if already has sub-items
        if target_item.sub_items:
            count = len(target_item.sub_items)
            return {
                "status": "error",
                "message": (
                    f"Item '{target_item.content}' already has {count} sub-items. "
                    "Clear them first to re-decompose."
                ),
            }

        # Build the decomposition prompt
        prompt_content = DECOMPOSE_SYSTEM_PROMPT.format(
            current_todos=self._get_current_todos_text(),
            task_content=target_item.content,
            context=context or "No additional context provided.",
        )

        try:
            from forge.llm.providers import ChatMessage

            # Call the LLM for decomposition
            model = self.config.decompose_model or self._smart_llm
            response = await self._llm_provider.create_chat_completion(
                model_prompt=[ChatMessage.user(prompt_content)],
                model_name=model,  # type: ignore[arg-type]
            )

            # Parse the JSON response
            response_text = response.response.content
            if not response_text:
                return {
                    "status": "error",
                    "message": "LLM returned empty response",
                }

            # Try to extract JSON from response (handle potential markdown wrapping)
            json_text = response_text.strip()
            if json_text.startswith("```"):
                # Remove markdown code blocks
                lines = json_text.split("\n")
                json_lines = []
                in_code = False
                for line in lines:
                    if line.startswith("```"):
                        in_code = not in_code
                        continue
                    if in_code or not line.startswith("```"):
                        json_lines.append(line)
                json_text = "\n".join(json_lines)

            decomposition = json.loads(json_text)

            # Validate response structure
            if "sub_items" not in decomposition:
                return {
                    "status": "error",
                    "message": "LLM response missing 'sub_items' field",
                }

            # Create sub-items
            new_sub_items = []
            for sub in decomposition["sub_items"]:
                if not sub.get("content") or not sub.get("active_form"):
                    continue
                new_sub_items.append(
                    TodoItem(
                        content=sub["content"],
                        active_form=sub["active_form"],
                        status="pending",
                    )
                )

            if not new_sub_items:
                return {
                    "status": "error",
                    "message": "LLM generated no valid sub-items",
                }

            # Update the target item with sub-items
            target_item.sub_items = new_sub_items

            return {
                "status": "success",
                "item": target_item.content,
                "sub_items_count": len(new_sub_items),
                "sub_items": [
                    {"content": s.content, "active_form": s.active_form}
                    for s in new_sub_items
                ],
                "summary": decomposition.get("summary", "Task decomposed successfully"),
            }

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM decomposition response: {e}")
            return {
                "status": "error",
                "message": f"Failed to parse LLM response as JSON: {e}",
            }
        except Exception as e:
            logger.error(f"Decomposition failed: {e}")
            return {
                "status": "error",
                "message": f"Decomposition failed: {e}",
            }