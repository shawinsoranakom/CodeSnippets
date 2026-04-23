async def test_gather_confirm_different_users_one_winner_no_hijack(self):
        # Different users racing the same token: still exactly one winner,
        # and the other gets a clean LinkTokenExpiredError (no partial state).
        fake_token = MagicMock(
            linkType=LinkType.SERVER.value,
            usedAt=None,
            expiresAt=datetime.now(timezone.utc) + timedelta(minutes=10),
            platform="DISCORD",
            platformServerId="g1",
            platformUserId="pu1",
            serverName="S1",
        )
        update_results = [1, 0]

        async def flaky_update_many(*args, **kwargs):
            return update_results.pop(0)

        created_link_user_ids: list[str] = []

        async def record_create(*, data):
            created_link_user_ids.append(data["userId"])
            return MagicMock()

        with (
            patch("backend.platform_linking.db.PlatformLinkToken") as mock_token,
            patch("backend.platform_linking.db.PlatformLink") as mock_link,
            patch("backend.platform_linking.db.transaction", new=_fake_transaction),
        ):
            mock_token.prisma.return_value.find_unique = AsyncMock(
                return_value=fake_token
            )
            mock_link.prisma.return_value.find_first = AsyncMock(return_value=None)
            mock_token.prisma.return_value.update_many = flaky_update_many
            mock_link.prisma.return_value.create = record_create

            results = await asyncio.gather(
                confirm_server_link("abc", "user-a"),
                confirm_server_link("abc", "user-b"),
                return_exceptions=True,
            )

        successes = [r for r in results if not isinstance(r, Exception)]
        losses = [r for r in results if isinstance(r, LinkTokenExpiredError)]
        assert len(successes) == 1
        assert len(losses) == 1
        assert len(created_link_user_ids) == 1
        assert created_link_user_ids[0] in ("user-a", "user-b")