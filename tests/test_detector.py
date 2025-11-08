"""Tests for rogvibe.utils.detector module."""

from unittest.mock import patch
from rogvibe.utils.detector import detect_default_participants


class TestDetector:
    """Test cases for detector module."""

    def test_detect_default_participants_no_providers(self):
        """Test when no providers are detected."""
        with patch("rogvibe.utils.detector.shutil.which") as mock_which:
            mock_which.return_value = None

            result = detect_default_participants()

            assert result == []
            # Should be called for each provider in MAYBE_VIBER
            assert mock_which.call_count > 0

    def test_detect_default_participants_less_than_4(self):
        """Test when less than 4 providers are detected."""
        with patch("rogvibe.utils.detector.shutil.which") as mock_which:
            # Return True for first 2 providers, False for others
            def which_side_effect(cmd):
                return "/usr/bin/" + cmd if cmd in ["kimi", "claude"] else None

            mock_which.side_effect = which_side_effect

            result = detect_default_participants()

            assert len(result) == 4
            assert "kimi" in result
            assert "claude" in result
            # Should have filler elements
            assert "lucky" in result or "handy" in result

    def test_detect_default_participants_between_5_and_8(self):
        """Test when between 5 and 8 providers are detected."""
        with patch("rogvibe.utils.detector.shutil.which") as mock_which:
            # Return True for first 6 providers, False for others
            providers = ["kimi", "claude", "gemini", "codex", "code", "cursor"]

            def which_side_effect(cmd):
                return "/usr/bin/" + cmd if cmd in providers else None

            mock_which.side_effect = which_side_effect

            result = detect_default_participants()

            assert len(result) == 8
            # All detected providers should be in result
            for provider in providers:
                assert provider in result
            # Should have filler elements
            assert "lucky" in result or "handy" in result

    def test_detect_default_participants_more_than_8(self):
        """Test when more than 8 providers are detected."""
        # Patch MAYBE_VIBER to have more than 8 elements
        extra_providers = [
            "kimi",
            "claude",
            "gemini",
            "codex",
            "code",
            "cursor",
            "amp",
            "opencode",
            "extra1",
            "extra2",
        ]
        with patch("rogvibe.utils.detector.MAYBE_VIBER", extra_providers):
            with patch("rogvibe.utils.detector.shutil.which") as mock_which:
                # Return True for all providers (more than 8)
                mock_which.return_value = "/usr/bin/provider"

                with patch("rogvibe.utils.detector.random.sample") as mock_sample:
                    mock_sample.return_value = [
                        "kimi",
                        "claude",
                        "gemini",
                        "codex",
                        "code",
                        "cursor",
                        "amp",
                        "opencode",
                    ]

                    result = detect_default_participants()

                    assert len(result) == 8
                    mock_sample.assert_called_once()

    def test_detect_default_participants_exactly_4(self):
        """Test when exactly 4 providers are detected."""
        with patch("rogvibe.utils.detector.shutil.which") as mock_which:
            # Return True for exactly 4 providers
            providers = ["kimi", "claude", "gemini", "codex"]

            def which_side_effect(cmd):
                return "/usr/bin/" + cmd if cmd in providers else None

            mock_which.side_effect = which_side_effect

            result = detect_default_participants()

            assert len(result) == 4
            # All detected providers should be in result
            for provider in providers:
                assert provider in result
            # Should not have filler elements (exactly 4 is the minimum)

    def test_detect_default_participants_exactly_8(self):
        """Test when exactly 8 providers are detected."""
        with patch("rogvibe.utils.detector.shutil.which") as mock_which:
            # Return True for exactly 8 providers
            providers = [
                "kimi",
                "claude",
                "gemini",
                "codex",
                "code",
                "cursor",
                "amp",
                "opencode",
            ]

            def which_side_effect(cmd):
                return "/usr/bin/" + cmd if cmd in providers else None

            mock_which.side_effect = which_side_effect

            result = detect_default_participants()

            assert len(result) == 8
            # All detected providers should be in result
            for provider in providers:
                assert provider in result

    def test_detect_default_participants_shuffling(self):
        """Test that providers are shuffled."""
        with patch("rogvibe.utils.detector.shutil.which") as mock_which:
            # Return True for 4 providers
            providers = ["kimi", "claude", "gemini", "codex"]

            def which_side_effect(cmd):
                return "/usr/bin/" + cmd if cmd in providers else None

            mock_which.side_effect = which_side_effect

            with patch("rogvibe.utils.detector.random.shuffle") as mock_shuffle:
                result = detect_default_participants()

                mock_shuffle.assert_called_once()
                assert len(result) == 4

    def test_detect_default_participants_random_sample(self):
        """Test random.sample is called when more than 8 providers."""
        # Patch MAYBE_VIBER to have more than 8 elements
        extra_providers = [
            "kimi",
            "claude",
            "gemini",
            "codex",
            "code",
            "cursor",
            "amp",
            "opencode",
            "extra1",
            "extra2",
        ]
        with patch("rogvibe.utils.detector.MAYBE_VIBER", extra_providers):
            with patch("rogvibe.utils.detector.shutil.which") as mock_which:
                # Return True for all providers (more than 8)
                mock_which.return_value = "/usr/bin/provider"

                with patch("rogvibe.utils.detector.random.sample") as mock_sample:
                    mock_sample.return_value = [
                        "kimi",
                        "claude",
                        "gemini",
                        "codex",
                        "code",
                        "cursor",
                        "amp",
                        "opencode",
                    ]

                    result = detect_default_participants()

                    mock_sample.assert_called_once()
                    assert len(result) == 8

    def test_internal_on_path_function(self):
        """Test the internal on_path function."""
        with patch("rogvibe.utils.detector.shutil.which") as mock_which:
            mock_which.side_effect = (
                lambda cmd: "/usr/bin/cmd" if cmd == "test_cmd" else None
            )

            # Test by calling detect_default_participants and checking behavior
            detect_default_participants()

            # Verify that shutil.which was called with the expected commands
            calls = [call[0][0] for call in mock_which.call_args_list]
            # Should include commands from MAYBE_VIBER
            assert len(calls) > 0

    @patch("rogvibe.utils.detector.MAYBE_VIBER", ["test1", "test2", "test3"])
    def test_with_custom_maybe_viber(self):
        """Test with custom MAYBE_VIBER list."""
        with patch("rogvibe.utils.detector.shutil.which") as mock_which:
            mock_which.side_effect = lambda cmd: cmd in ["test1", "test2"]

            result = detect_default_participants()

            assert len(result) == 4
            assert "test1" in result
            assert "test2" in result
            # Should have fillers
            assert "lucky" in result or "handy" in result
