"""Pytest configuration and fixtures for rogvibe tests."""

import pytest
from unittest.mock import Mock


@pytest.fixture
def mock_app():
    """Create a mock Textual app for testing."""
    app = Mock()
    app.suspend = Mock()
    app.exit = Mock()
    return app


@pytest.fixture
def mock_widget():
    """Create a mock Textual widget for testing."""
    widget = Mock()
    return widget
