"""Tests for rogvibe.app module."""

from unittest.mock import Mock, patch
from rogvibe.app import run, run_slot_machine, run_flip_card, DEFAULT_PARTICIPANTS


class TestApp:
    """Test cases for app module functions."""

    def test_run_with_none_participants(self):
        """Test run function with None participants."""
        with patch("rogvibe.app.LotteryApp") as mock_lottery_app:
            mock_instance = Mock()
            mock_lottery_app.return_value = mock_instance

            run(None)

            # Should use DEFAULT_PARTICIPANTS
            mock_lottery_app.assert_called_once_with(list(DEFAULT_PARTICIPANTS))
            mock_instance.run.assert_called_once()

    def test_run_with_empty_participants(self):
        """Test run function with empty participants."""
        with patch("rogvibe.app.LotteryApp") as mock_lottery_app:
            mock_instance = Mock()
            mock_lottery_app.return_value = mock_instance

            run([])

            # Should use DEFAULT_PARTICIPANTS
            mock_lottery_app.assert_called_once_with(list(DEFAULT_PARTICIPANTS))
            mock_instance.run.assert_called_once()

    def test_run_with_valid_participants(self):
        """Test run function with valid participants."""
        participants = ["user1", "user2", "user3", "user4"]

        with patch("rogvibe.app.LotteryApp") as mock_lottery_app:
            mock_instance = Mock()
            mock_lottery_app.return_value = mock_instance

            run(participants)

            mock_lottery_app.assert_called_once_with(participants)
            mock_instance.run.assert_called_once()

    def test_run_with_whitespace_participants(self):
        """Test run function with participants containing whitespace."""
        participants = ["  user1  ", "", "  user2  ", "   "]
        expected = ["user1", "user2"]

        with patch("rogvibe.app.LotteryApp") as mock_lottery_app:
            mock_instance = Mock()
            mock_lottery_app.return_value = mock_instance

            run(participants)

            mock_lottery_app.assert_called_once_with(expected)
            mock_instance.run.assert_called_once()

    def test_run_slot_machine(self):
        """Test run_slot_machine function."""
        with patch("rogvibe.app.SlotMachineApp") as mock_slot_app:
            mock_instance = Mock()
            mock_slot_app.return_value = mock_instance

            run_slot_machine()

            mock_slot_app.assert_called_once()
            mock_instance.run.assert_called_once()

    def test_run_flip_card(self):
        """Test run_flip_card function."""
        with patch("rogvibe.app.FlipCardApp") as mock_flip_app:
            mock_instance = Mock()
            mock_flip_app.return_value = mock_instance

            run_flip_card()

            mock_flip_app.assert_called_once()
            mock_instance.run.assert_called_once()

    def test_default_participants_import(self):
        """Test that DEFAULT_PARTICIPANTS is properly imported."""
        assert DEFAULT_PARTICIPANTS is not None
        assert isinstance(DEFAULT_PARTICIPANTS, list)
        assert len(DEFAULT_PARTICIPANTS) > 0

    def test_default_participants_with_detection(self):
        """Test DEFAULT_PARTICIPANTS when detection returns values."""
        # Use actual provider names from MAYBE_VIBER
        detected_providers = ["kimi", "claude", "gemini", "codex"]
        # Mock shutil.which to detect specific providers
        with patch("rogvibe.utils.detector.shutil.which") as mock_which:

            def which_side_effect(cmd):
                return "/usr/bin/" + cmd if cmd in detected_providers else None

            mock_which.side_effect = which_side_effect

            # Re-import to trigger the detection logic
            import importlib
            import rogvibe.app

            importlib.reload(rogvibe.app)

            # Should use detected participants (4 detected, so exactly 4 returned)
            assert len(rogvibe.app.DEFAULT_PARTICIPANTS) == 4
            for provider in detected_providers:
                assert provider in rogvibe.app.DEFAULT_PARTICIPANTS

    def test_default_participants_fallback(self):
        """Test DEFAULT_PARTICIPANTS when detection returns empty."""
        # Mock shutil.which to detect no providers
        with patch("rogvibe.utils.detector.shutil.which") as mock_which:
            mock_which.return_value = None

            # Re-import to trigger the detection logic
            import importlib
            import rogvibe.app
            from rogvibe.constants import FALLBACK_DEFAULTS

            importlib.reload(rogvibe.app)

            # Should fall back to FALLBACK_DEFAULTS
            assert rogvibe.app.DEFAULT_PARTICIPANTS == list(FALLBACK_DEFAULTS)
