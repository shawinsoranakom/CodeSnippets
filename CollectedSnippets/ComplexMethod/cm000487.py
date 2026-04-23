async def update_user_onboarding(user_id: str, data: UserOnboardingUpdate):
    update: UserOnboardingUpdateInput = {}
    onboarding = await get_user_onboarding(user_id)
    if data.walletShown:
        update["walletShown"] = data.walletShown
    if data.notified is not None:
        update["notified"] = list(set(data.notified + onboarding.notified))
    if data.usageReason is not None:
        update["usageReason"] = data.usageReason
    if data.integrations is not None:
        update["integrations"] = data.integrations
    if data.otherIntegrations is not None:
        update["otherIntegrations"] = data.otherIntegrations
    if data.selectedStoreListingVersionId is not None:
        update["selectedStoreListingVersionId"] = data.selectedStoreListingVersionId
    if data.agentInput is not None:
        update["agentInput"] = SafeJson(data.agentInput)
    if data.onboardingAgentExecutionId is not None:
        update["onboardingAgentExecutionId"] = data.onboardingAgentExecutionId

    return await UserOnboarding.prisma().upsert(
        where={"userId": user_id},
        data={
            "create": {"userId": user_id, **update},
            "update": update,
        },
    )