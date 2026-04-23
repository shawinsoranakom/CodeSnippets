async def _reward_user(user_id: str, onboarding: UserOnboarding, step: OnboardingStep):
    reward = 0
    match step:
        # Welcome bonus for visiting copilot ($5 = 500 credits)
        case OnboardingStep.VISIT_COPILOT:
            reward = 500
        # Reward user when they clicked New Run during onboarding
        # This is because they need credits before scheduling a run (next step)
        # This is seen as a reward for the GET_RESULTS step in the wallet
        case OnboardingStep.AGENT_NEW_RUN:
            reward = 300
        case OnboardingStep.MARKETPLACE_VISIT:
            reward = 100
        case OnboardingStep.MARKETPLACE_ADD_AGENT:
            reward = 100
        case OnboardingStep.MARKETPLACE_RUN_AGENT:
            reward = 100
        case OnboardingStep.BUILDER_SAVE_AGENT:
            reward = 100
        case OnboardingStep.RE_RUN_AGENT:
            reward = 100
        case OnboardingStep.SCHEDULE_AGENT:
            reward = 100
        case OnboardingStep.RUN_AGENTS:
            reward = 300
        case OnboardingStep.RUN_3_DAYS:
            reward = 100
        case OnboardingStep.TRIGGER_WEBHOOK:
            reward = 100
        case OnboardingStep.RUN_14_DAYS:
            reward = 300
        case OnboardingStep.RUN_AGENTS_100:
            reward = 300

    if reward == 0:
        return

    # Skip if already rewarded
    if step in onboarding.rewardedFor:
        return

    user_credit_model = await get_user_credit_model(user_id)
    await user_credit_model.onboarding_reward(user_id, reward, step)
    await UserOnboarding.prisma().update(
        where={"userId": user_id},
        data={
            "rewardedFor": list(set(onboarding.rewardedFor + [step])),
        },
    )