def test_converts_skill_with_keyword_trigger(self):
        """Test converting skill data with keyword triggers."""
        # Arrange
        skill_info = SkillInfo(
            name='test_skill',
            content='Test content',
            triggers=['test', 'testing'],
            source='repo',
            description='A test skill',
        )

        # Act
        skill = _convert_skill_info_to_skill(skill_info)

        # Assert
        assert isinstance(skill, Skill)
        assert skill.name == 'test_skill'
        assert skill.content == 'Test content'
        assert isinstance(skill.trigger, KeywordTrigger)
        assert skill.trigger.keywords == ['test', 'testing']
        assert skill.source == 'repo'
        assert skill.description == 'A test skill'