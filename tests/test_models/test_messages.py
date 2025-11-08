"""Tests for rogvibe.models.messages module."""

from unittest.mock import Mock
from textual.widget import Widget
from rogvibe.models.messages import (
    SpinFinished,
    SpinTick,
    SlotReelSpinning,
    SlotReelStopped,
    SlotAllStopped,
    AllCardsMatched,
    PairMatched,
)


class TestMessages:
    """Test cases for message classes."""

    def test_spin_finished_message(self):
        """Test SpinFinished message creation and properties."""
        mock_widget = Mock(spec=Widget)
        winner = "test_winner"

        msg = SpinFinished(mock_widget, winner)

        assert msg.winner == winner
        assert msg.origin == mock_widget

    def test_spin_tick_message(self):
        """Test SpinTick message creation and properties."""
        mock_widget = Mock(spec=Widget)
        dice_face = "⚀"

        msg = SpinTick(mock_widget, dice_face)

        assert msg.dice_face == dice_face
        assert msg.origin == mock_widget

    def test_slot_reel_spinning_message(self):
        """Test SlotReelSpinning message creation and properties."""
        mock_widget = Mock(spec=Widget)
        reel_index = 0
        value = "test_value"

        msg = SlotReelSpinning(mock_widget, reel_index, value)

        assert msg.reel_index == reel_index
        assert msg.value == value
        assert msg.origin == mock_widget

    def test_slot_reel_stopped_message(self):
        """Test SlotReelStopped message creation and properties."""
        mock_widget = Mock(spec=Widget)
        reel_index = 2
        value = "stopped_value"

        msg = SlotReelStopped(mock_widget, reel_index, value)

        assert msg.reel_index == reel_index
        assert msg.value == value
        assert msg.origin == mock_widget

    def test_slot_all_stopped_message(self):
        """Test SlotAllStopped message creation and properties."""
        mock_widget = Mock(spec=Widget)
        results = ["val1", "val2", "val3"]

        msg = SlotAllStopped(mock_widget, results)

        assert msg.results == results
        assert msg.origin == mock_widget

    def test_all_cards_matched_message(self):
        """Test AllCardsMatched message creation and properties."""
        mock_widget = Mock(spec=Widget)
        winner = "card_winner"

        msg = AllCardsMatched(mock_widget, winner)

        assert msg.winner == winner
        assert msg.origin == mock_widget

    def test_pair_matched_message(self):
        """Test PairMatched message creation and properties."""
        mock_widget = Mock(spec=Widget)
        value = "pair_value"

        msg = PairMatched(mock_widget, value)

        assert msg.value == value
        assert msg.origin == mock_widget
