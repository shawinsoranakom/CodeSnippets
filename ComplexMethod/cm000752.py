async def run(
        self,
        input_data: Input,
        *,
        credentials: SmartLeadCredentials,
        **kwargs,
    ) -> BlockOutput:
        response = await self.add_leads_to_campaign(
            input_data.campaign_id, input_data.lead_list, credentials
        )
        self.merge_stats(
            NodeExecutionStats(
                provider_cost=float(len(input_data.lead_list)),
                provider_cost_type="items",
            )
        )

        yield "campaign_id", input_data.campaign_id
        yield "upload_count", response.upload_count
        if response.already_added_to_campaign:
            yield "already_added_to_campaign", response.already_added_to_campaign
        if response.duplicate_count:
            yield "duplicate_count", response.duplicate_count
        if response.invalid_email_count:
            yield "invalid_email_count", response.invalid_email_count
        if response.is_lead_limit_exhausted:
            yield "is_lead_limit_exhausted", response.is_lead_limit_exhausted
        if response.lead_import_stopped_count:
            yield "lead_import_stopped_count", response.lead_import_stopped_count
        if response.error:
            yield "error", response.error
        if not response.ok:
            yield "error", "Failed to add leads to campaign"