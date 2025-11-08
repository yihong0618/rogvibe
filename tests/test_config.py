"""Tests for rogvibe.config module."""


class TestConfig:
    """Test cases for config module."""

    def test_maybe_viber_import(self):
        """Test that MAYBE_VIBER can be imported from config."""
        from rogvibe.config import MAYBE_VIBER

        assert MAYBE_VIBER is not None
        assert isinstance(MAYBE_VIBER, list)
        assert len(MAYBE_VIBER) > 0

    def test_config_exports(self):
        """Test that config module exports expected items."""
        from rogvibe import config

        assert hasattr(config, "MAYBE_VIBER")
        assert hasattr(config, "__all__")
        assert "MAYBE_VIBER" in config.__all__
