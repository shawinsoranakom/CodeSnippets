async def test_returns_claims_for_organization(self, org_id, user_id, make_claim):
        """
        GIVEN: An organization with multiple Git claims
        WHEN: GET /api/organizations/{org_id}/git-claims is called
        THEN: All claims are returned with correct details
        """
        claim1 = make_claim(org_id, provider='github', git_organization='OpenHands')
        claim2 = make_claim(org_id, provider='gitlab', git_organization='AcmeCo')

        with patch(
            'server.routes.orgs.OrgGitClaimStore.get_claims_by_org_id',
            AsyncMock(return_value=[claim1, claim2]),
        ):
            result = await get_git_claims(org_id=org_id, user_id=user_id)

        assert len(result) == 2
        assert result[0].id == str(claim1.id)
        assert result[0].org_id == str(org_id)
        assert result[0].provider == 'github'
        assert result[0].git_organization == 'OpenHands'
        assert result[0].claimed_by == str(claim1.claimed_by)
        assert result[0].claimed_at == '2026-04-01T12:00:00'
        assert result[1].id == str(claim2.id)
        assert result[1].provider == 'gitlab'
        assert result[1].git_organization == 'AcmeCo'