def from_db(cls, prisma_user: "PrismaUser") -> "User":
        """Convert a database User object to application User model."""
        # Handle metadata field - convert from JSON string or dict to dict
        metadata = {}
        if prisma_user.metadata:
            if isinstance(prisma_user.metadata, str):
                try:
                    metadata = json_loads(prisma_user.metadata)
                except (JSONDecodeError, TypeError):
                    metadata = {}
            elif isinstance(prisma_user.metadata, dict):
                metadata = prisma_user.metadata

        # Handle topUpConfig field
        top_up_config = None
        if prisma_user.topUpConfig:
            if isinstance(prisma_user.topUpConfig, str):
                try:
                    config_dict = json_loads(prisma_user.topUpConfig)
                    top_up_config = AutoTopUpConfig.model_validate(config_dict)
                except (JSONDecodeError, TypeError, ValueError):
                    top_up_config = None
            elif isinstance(prisma_user.topUpConfig, dict):
                try:
                    top_up_config = AutoTopUpConfig.model_validate(
                        prisma_user.topUpConfig
                    )
                except ValueError:
                    top_up_config = None

        return cls(
            id=prisma_user.id,
            email=prisma_user.email,
            email_verified=prisma_user.emailVerified or True,
            name=prisma_user.name,
            created_at=prisma_user.createdAt,
            updated_at=prisma_user.updatedAt,
            metadata=metadata,
            integrations=prisma_user.integrations or "",
            stripe_customer_id=prisma_user.stripeCustomerId,
            top_up_config=top_up_config,
            subscription_tier=prisma_user.subscriptionTier or SubscriptionTier.FREE,
            max_emails_per_day=prisma_user.maxEmailsPerDay or 3,
            notify_on_agent_run=prisma_user.notifyOnAgentRun or True,
            notify_on_zero_balance=prisma_user.notifyOnZeroBalance or True,
            notify_on_low_balance=prisma_user.notifyOnLowBalance or True,
            notify_on_block_execution_failed=prisma_user.notifyOnBlockExecutionFailed
            or True,
            notify_on_continuous_agent_error=prisma_user.notifyOnContinuousAgentError
            or True,
            notify_on_daily_summary=prisma_user.notifyOnDailySummary or True,
            notify_on_weekly_summary=prisma_user.notifyOnWeeklySummary or True,
            notify_on_monthly_summary=prisma_user.notifyOnMonthlySummary or True,
            timezone=prisma_user.timezone or USER_TIMEZONE_NOT_SET,
        )