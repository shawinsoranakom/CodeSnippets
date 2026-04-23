async def _add_transaction(
        self,
        user_id: str,
        amount: int,
        transaction_type: CreditTransactionType,
        is_active: bool = True,
        transaction_key: str | None = None,
        ceiling_balance: int | None = None,
        fail_insufficient_credits: bool = True,
        metadata: SafeJson = SafeJson({}),
    ) -> tuple[int, str]:
        """
        Add a new transaction for the user.
        This is the only method that should be used to add a new transaction.

        ATOMIC OPERATION DESIGN DECISION:
        ================================
        This method uses PostgreSQL row-level locking (FOR UPDATE) for atomic credit operations.
        After extensive analysis of concurrency patterns and correctness requirements, we determined
        that the FOR UPDATE approach is necessary despite the latency overhead.

        WHY FOR UPDATE LOCKING IS REQUIRED:
        ----------------------------------
        1. **Data Consistency**: Credit operations must be ACID-compliant. The balance check,
           calculation, and update must be atomic to prevent race conditions where:
           - Multiple spend operations could exceed available balance
           - Lost update problems could occur with concurrent top-ups
           - Refunds could create negative balances incorrectly

        2. **Serializability**: FOR UPDATE ensures operations are serialized at the database level,
           guaranteeing that each transaction sees a consistent view of the balance before applying changes.

        3. **Correctness Over Performance**: Financial operations require absolute correctness.
           The ~10-50ms latency increase from row locking is acceptable for the guarantee that
           no user will ever have an incorrect balance due to race conditions.

        4. **PostgreSQL Optimization**: Modern PostgreSQL versions optimize row locks efficiently.
           The performance cost is minimal compared to the complexity and risk of lock-free approaches.

        ALTERNATIVES CONSIDERED AND REJECTED:
        ------------------------------------
        - **Optimistic Concurrency**: Using version numbers or timestamps would require complex
          retry logic and could still fail under high contention scenarios.
        - **Application-Level Locking**: Redis locks or similar would add network overhead and
          single points of failure while being less reliable than database locks.
        - **Event Sourcing**: Would require complete architectural changes and eventual consistency
          models that don't fit our real-time balance requirements.

        PERFORMANCE CHARACTERISTICS:
        ---------------------------
        - Single user operations: 10-50ms latency (acceptable for financial operations)
        - Concurrent operations on same user: Serialized (prevents data corruption)
        - Concurrent operations on different users: Fully parallel (no blocking)

        This design prioritizes correctness and data integrity over raw performance,
        which is the appropriate choice for a credit/payment system.

        Args:
            user_id (str): The user ID.
            amount (int): The amount of credits to add.
            transaction_type (CreditTransactionType): The type of transaction.
            is_active (bool): Whether the transaction is active or needs to be manually activated through _enable_transaction.
            transaction_key (str | None): The transaction key. Avoids adding transaction if the key already exists.
            ceiling_balance (int | None): The ceiling balance. Avoids adding more credits if the balance is already above the ceiling.
            fail_insufficient_credits (bool): Whether to fail if the user has insufficient credits.
            metadata (Json): The metadata of the transaction.

        Returns:
            tuple[int, str]: The new balance & the transaction key.
        """
        # Quick validation for ceiling balance to avoid unnecessary database operations
        if ceiling_balance and amount > 0:
            current_balance, _ = await self._get_credits(user_id)
            if current_balance >= ceiling_balance:
                raise ValueError(
                    f"You already have enough balance of ${current_balance / 100}, top-up is not required when you already have at least ${ceiling_balance / 100}"
                )

        # Single unified atomic operation for all transaction types using UserBalance
        try:
            result = await query_raw_with_schema(
                """
                WITH user_balance_lock AS (
                    SELECT 
                        $1::text as userId, 
                        -- CRITICAL: FOR UPDATE lock prevents concurrent modifications to the same user's balance
                        -- This ensures atomic read-modify-write operations and prevents race conditions
                        COALESCE(
                            (SELECT balance FROM {schema_prefix}"UserBalance" WHERE "userId" = $1 FOR UPDATE),
                            -- Fallback: compute balance from transaction history if UserBalance doesn't exist
                            (SELECT COALESCE(ct."runningBalance", 0) 
                             FROM {schema_prefix}"CreditTransaction" ct 
                             WHERE ct."userId" = $1 
                               AND ct."isActive" = true 
                               AND ct."runningBalance" IS NOT NULL 
                             ORDER BY ct."createdAt" DESC 
                             LIMIT 1),
                            0
                        ) as balance
                ),
                balance_update AS (
                    INSERT INTO {schema_prefix}"UserBalance" ("userId", "balance", "updatedAt")
                    SELECT 
                        $1::text,
                        CASE 
                            -- For inactive transactions: Don't update balance
                            WHEN $5::boolean = false THEN user_balance_lock.balance
                            -- For ceiling balance (amount > 0): Apply ceiling
                            WHEN $2 > 0 AND $7::int IS NOT NULL AND user_balance_lock.balance > $7::int - $2 THEN $7::int
                            -- For regular operations: Apply with overflow/underflow protection  
                            WHEN user_balance_lock.balance + $2 > $6::int THEN $6::int
                            WHEN user_balance_lock.balance + $2 < $10::int THEN $10::int
                            ELSE user_balance_lock.balance + $2
                        END,
                        CURRENT_TIMESTAMP
                    FROM user_balance_lock
                    WHERE (
                        $5::boolean = false OR  -- Allow inactive transactions
                        $2 >= 0 OR              -- Allow positive amounts (top-ups, grants)
                        $8::boolean = false OR  -- Allow when insufficient balance check is disabled
                        user_balance_lock.balance + $2 >= 0  -- Allow spending only when sufficient balance
                    )
                    ON CONFLICT ("userId") DO UPDATE SET
                        "balance" = EXCLUDED."balance",
                        "updatedAt" = EXCLUDED."updatedAt"
                    RETURNING "balance", "updatedAt"
                ),
                transaction_insert AS (
                    INSERT INTO {schema_prefix}"CreditTransaction" (
                        "userId", "amount", "type", "runningBalance", 
                        "metadata", "isActive", "createdAt", "transactionKey"
                    )
                    SELECT 
                        $1::text,
                        $2::int,
                        $3::text::{schema_prefix}"CreditTransactionType",
                        CASE 
                            -- For inactive transactions: Set runningBalance to original balance (don't apply the change yet)
                            WHEN $5::boolean = false THEN user_balance_lock.balance
                            ELSE COALESCE(balance_update.balance, user_balance_lock.balance)
                        END,
                        $4::jsonb,
                        $5::boolean,
                        COALESCE(balance_update."updatedAt", CURRENT_TIMESTAMP),
                        COALESCE($9, gen_random_uuid()::text)
                    FROM user_balance_lock
                    LEFT JOIN balance_update ON true
                    WHERE (
                        $5::boolean = false OR  -- Allow inactive transactions
                        $2 >= 0 OR              -- Allow positive amounts (top-ups, grants)
                        $8::boolean = false OR  -- Allow when insufficient balance check is disabled
                        user_balance_lock.balance + $2 >= 0  -- Allow spending only when sufficient balance
                    )
                    RETURNING "runningBalance", "transactionKey"
                )
                SELECT "runningBalance" as balance, "transactionKey" FROM transaction_insert;
                """,
                user_id,  # $1
                amount,  # $2
                transaction_type.value,  # $3
                dumps(metadata.data),  # $4 - use pre-serialized JSON string for JSONB
                is_active,  # $5
                POSTGRES_INT_MAX,  # $6 - overflow protection
                ceiling_balance,  # $7 - ceiling balance (nullable)
                fail_insufficient_credits,  # $8 - check balance for spending
                transaction_key,  # $9 - transaction key (nullable)
                POSTGRES_INT_MIN,  # $10 - underflow protection
            )
        except Exception as e:
            # Convert raw SQL unique constraint violations to UniqueViolationError
            # for consistent exception handling throughout the codebase
            error_str = str(e).lower()
            if (
                "already exists" in error_str
                or "duplicate key" in error_str
                or "unique constraint" in error_str
            ):
                # Extract table and constraint info for better error messages
                # Re-raise as a UniqueViolationError but with proper format
                # Create a minimal data structure that the error constructor expects
                raise UniqueViolationError({"error": str(e), "user_facing_error": {}})
            # For any other error, re-raise as-is
            raise

        if result:
            new_balance, tx_key = result[0]["balance"], result[0]["transactionKey"]
            # UserBalance is already updated by the CTE

            # Clear insufficient funds notification flags when credits are added
            # so user can receive alerts again if they run out in the future.
            if (
                amount > 0
                and is_active
                and transaction_type
                in [CreditTransactionType.GRANT, CreditTransactionType.TOP_UP]
            ):
                # Lazy import to avoid circular dependency with executor.manager
                from backend.executor.billing import (
                    clear_insufficient_funds_notifications,
                )

                await clear_insufficient_funds_notifications(user_id)

            return new_balance, tx_key

        # If no result, either user doesn't exist or insufficient balance
        user = await User.prisma().find_unique(where={"id": user_id})
        if not user:
            raise ValueError(f"User {user_id} not found")

        # Must be insufficient balance for spending operation
        if amount < 0 and fail_insufficient_credits:
            current_balance, _ = await self._get_credits(user_id)
            raise InsufficientBalanceError(
                message=f"Insufficient balance of ${current_balance / 100}, where this will cost ${abs(amount) / 100}",
                user_id=user_id,
                balance=current_balance,
                amount=amount,
            )

        # Unexpected case
        raise ValueError(f"Transaction failed for user {user_id}, amount {amount}")