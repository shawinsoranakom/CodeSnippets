def _update_costs(self, usage: Union[dict, BaseModel], model: str = None, local_calc_usage: bool = True):
        """update each request's token cost
        Args:
            model (str): model name or in some scenarios called endpoint
            local_calc_usage (bool): some models don't calculate usage, it will overwrite LLMConfig.calc_usage
        """
        calc_usage = self.config.calc_usage and local_calc_usage
        model = model or self.pricing_plan
        model = model or self.model
        usage = usage.model_dump() if isinstance(usage, BaseModel) else usage
        if calc_usage and self.cost_manager and usage:
            try:
                prompt_tokens = int(usage.get("prompt_tokens", 0))
                completion_tokens = int(usage.get("completion_tokens", 0))
                self.cost_manager.update_cost(prompt_tokens, completion_tokens, model)
            except Exception as e:
                logger.error(f"{self.__class__.__name__} updates costs failed! exp: {e}")