async def _prepare_payload(cls, model: str, message: str) -> Dict[str, Any]:
        # Map model names to API model names
        api_model = "grok-latest"

        if model in ["grok-4", "grok-4-heavy", "grok-4-reasoning"]:
            api_model = model
        elif model == "grok-3":
            api_model = "grok-3"
        elif model in ["grok-3-mini", "grok-3-mini-reasoning"]:
            api_model = "grok-3-mini"
        elif model == "grok-2":
            api_model = "grok-2"

        # Check if it's a reasoning model
        is_reasoning = model.endswith("-reasoning") or model.endswith("-thinking") or model.endswith("-r1")

        # Enable Big Brain mode for heavy models
        enable_big_brain = "heavy" in model or "big-brain" in model

        # Enable DeepSearch for Grok 3+ models
        enable_deep_search = not model.startswith("grok-2")

        return {
            "temporary": True,
            "modelName": api_model,
            "message": message,
            "fileAttachments": [],
            "imageAttachments": [],
            "disableSearch": False,
            "enableImageGeneration": model == "grok-2-image" or model == "grok-4",
            "returnImageBytes": False,
            "returnRawGrokInXaiRequest": False,
            "enableImageStreaming": True,
            "imageGenerationCount": 2,
            "forceConcise": False,
            "toolOverrides": {},
            "enableSideBySide": True,
            "isPreset": False,
            "sendFinalMetadata": True,
            "customInstructions": "",
            "deepsearchPreset": "enabled" if enable_deep_search else "",
            "isReasoning": is_reasoning,
            "enableBigBrain": enable_big_brain,
            "enableLiveSearch": False,  # Real-time search for Grok 4
            "contextWindow": 256000 if model.startswith("grok-4") else 131072,  # 256k for Grok 4, 128k for others
        }