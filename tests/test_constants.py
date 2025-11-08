"""Tests for rogvibe.constants module."""

from rogvibe.constants import (
    FALLBACK_DEFAULTS,
    MAYBE_VIBER,
    ANIMATION_COLORS,
    BORDER_COLORS,
    CELEBRATION_EMOJIS,
    DICE_FACES,
    DICE_EMOJI,
    TARGET_EMOJI,
    SPECIAL_PARTICIPANTS,
)


class TestConstants:
    """Test cases for constants."""

    def test_fallback_defaults(self):
        """Test FALLBACK_DEFAULTS constant."""
        assert isinstance(FALLBACK_DEFAULTS, list)
        assert len(FALLBACK_DEFAULTS) == 4
        assert all(name == "handy" for name in FALLBACK_DEFAULTS)

    def test_maybe_viber(self):
        """Test MAYBE_VIBER constant."""
        assert isinstance(MAYBE_VIBER, list)
        assert len(MAYBE_VIBER) > 0
        expected_commands = [
            "kimi",
            "claude",
            "gemini",
            "codex",
            "code",
            "cursor",
            "amp",
            "opencode",
        ]
        for cmd in expected_commands:
            assert cmd in MAYBE_VIBER

    def test_animation_colors(self):
        """Test ANIMATION_COLORS constant."""
        assert isinstance(ANIMATION_COLORS, list)
        assert len(ANIMATION_COLORS) > 0
        expected_colors = ["yellow", "red", "magenta", "cyan", "white"]
        for color in expected_colors:
            assert color in ANIMATION_COLORS

    def test_border_colors(self):
        """Test BORDER_COLORS constant."""
        assert isinstance(BORDER_COLORS, list)
        assert len(BORDER_COLORS) > 0
        expected_colors = ["yellow", "red", "magenta", "cyan", "green"]
        for color in expected_colors:
            assert color in BORDER_COLORS

    def test_celebration_emojis(self):
        """Test CELEBRATION_EMOJIS constant."""
        assert isinstance(CELEBRATION_EMOJIS, list)
        assert len(CELEBRATION_EMOJIS) > 0
        expected_emojis = ["✨", "🌟", "⭐", "💫", "🎉", "🎊", "🎈"]
        for emoji in expected_emojis:
            assert emoji in CELEBRATION_EMOJIS

    def test_dice_faces(self):
        """Test DICE_FACES constant."""
        assert isinstance(DICE_FACES, list)
        assert len(DICE_FACES) == 6
        expected_faces = ["⚀", "⚁", "⚂", "⚃", "⚄", "⚅"]
        for face in expected_faces:
            assert face in DICE_FACES

    def test_dice_emoji(self):
        """Test DICE_EMOJI constant."""
        assert isinstance(DICE_EMOJI, str)
        assert DICE_EMOJI == "🎲"

    def test_target_emoji(self):
        """Test TARGET_EMOJI constant."""
        assert isinstance(TARGET_EMOJI, str)
        assert TARGET_EMOJI == "🎯"

    def test_special_participants(self):
        """Test SPECIAL_PARTICIPANTS constant."""
        assert isinstance(SPECIAL_PARTICIPANTS, set)
        expected_special = {"lucky", "handy"}
        assert SPECIAL_PARTICIPANTS == expected_special

    def test_constants_immutability(self):
        """Test that constants are not accidentally modified."""
        # Test that we can't modify the constants (they should be treated as immutable)
        original_fallback = FALLBACK_DEFAULTS.copy()
        original_viber = MAYBE_VIBER.copy()
        original_colors = ANIMATION_COLORS.copy()

        # Try to modify (this should not affect the original constants)
        test_fallback = FALLBACK_DEFAULTS.copy()
        test_fallback.append("modified")
        assert len(FALLBACK_DEFAULTS) == len(original_fallback)

        test_viber = MAYBE_VIBER.copy()
        test_viber.append("modified")
        assert len(MAYBE_VIBER) == len(original_viber)

        test_colors = ANIMATION_COLORS.copy()
        test_colors.append("modified")
        assert len(ANIMATION_COLORS) == len(original_colors)

    def test_no_empty_constants(self):
        """Test that no constant lists are empty."""
        assert len(FALLBACK_DEFAULTS) > 0
        assert len(MAYBE_VIBER) > 0
        assert len(ANIMATION_COLORS) > 0
        assert len(BORDER_COLORS) > 0
        assert len(CELEBRATION_EMOJIS) > 0
        assert len(DICE_FACES) > 0
        assert len(SPECIAL_PARTICIPANTS) > 0
