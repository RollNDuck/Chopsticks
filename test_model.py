# test_model.py
"""Unit tests for Chopsticks model."""
import pytest
from model import ChopsticksModel
from required_types import PlayerId, HandId, TapVariant, WinVariant
from hand_info import HandInfoImpl

def test_hand_info_to_method():
    """Test HandInfo to() method behavior."""
    hand = HandInfoImpl(HandId(0), PlayerId(0), 2)
    assert hand.to(3) is not None
    assert hand.to(0) is None
    assert hand.to(-1) is None
    assert hand.to(6) is None

def test_initial_state():
    """Test game initializes correctly."""
    model = ChopsticksModel.make(2, TapVariant.CUTOFF, WinVariant.STANDARD)
    assert model.current_player_id == PlayerId(0)
    hands = model.get_player_hands(PlayerId(0))
    assert len(hands) == 2
    assert all(h.fingers_up == 1 for h in hands)

def test_tap_exactly_five_fingers():
    """Test tap that results in exactly 5 fingers."""
    model = ChopsticksModel.make(2, TapVariant.CUTOFF, WinVariant.STANDARD)
    for _ in range(3):
        model.do_tap(HandId(0), (PlayerId(0), HandId(0)))
    result = model.do_tap(HandId(0), (PlayerId(1), HandId(0)))
    assert result is True
    target_hand = model.get_player_hands(PlayerId(1))[0]
    assert target_hand.fingers_up == 0

def test_tap_cutoff_variant():
    """Test cutoff variant behavior."""
    model = ChopsticksModel.make(2, TapVariant.CUTOFF, WinVariant.STANDARD)
    for _ in range(3):
        model.do_tap(HandId(0), (PlayerId(0), HandId(0)))
    result = model.do_tap(HandId(0), (PlayerId(1), HandId(0)))
    assert result is True
    target_hand = model.get_player_hands(PlayerId(1))[0]
    assert target_hand.fingers_up == 0

def test_tap_rollover_variant():
    """Test rollover variant behavior."""
    model = ChopsticksModel.make(2, TapVariant.ROLLOVER, WinVariant.STANDARD)
    for _ in range(3):
        model.do_tap(HandId(0), (PlayerId(0), HandId(0)))
    result = model.do_tap(HandId(0), (PlayerId(1), HandId(0)))
    assert result is True
    target_hand = model.get_player_hands(PlayerId(1))[0]
    assert target_hand.fingers_up == 0

def test_split_action():
    """Test valid split action."""
    model = ChopsticksModel.make(2, TapVariant.CUTOFF, WinVariant.STANDARD)
    model.do_tap(HandId(0), (PlayerId(1), HandId(0)))
    # Manually advance turn twice to get back to player 0
    model._next_player()
    model._next_player()
    result = model.do_split(HandId(0), HandId(1), 1)
    assert result is True
    hands = model.get_player_hands(PlayerId(0))
    assert hands[0].fingers_up == 1
    assert hands[1].fingers_up == 2

def test_invalid_split():
    """Test invalid split attempt."""
    model = ChopsticksModel.make(2, TapVariant.CUTOFF, WinVariant.STANDARD)
    result = model.do_split(HandId(0), HandId(1), 1)
    assert result is False

def test_winner_standard_variant():
    """Test standard win condition."""
    model = ChopsticksModel.make(2, TapVariant.CUTOFF, WinVariant.STANDARD)
    for hand_id in [HandId(0), HandId(1)]:
        for _ in range(3):
            model.do_tap(HandId(0), (PlayerId(1), hand_id))
    winner = model.get_winner()
    assert winner == PlayerId(0)

def test_misere_a_variant():
    """Test misere A win condition."""
    model = ChopsticksModel.make(3, TapVariant.CUTOFF, WinVariant.MISERE_A)
    for hand_id in [HandId(0), HandId(1)]:
        for _ in range(3):
            model.do_tap(HandId(0), (PlayerId(0), hand_id))
    winner = model.get_winner()
    assert winner == PlayerId(0)

def test_misere_b_variant():
    """Test misere B win condition."""
    model = ChopsticksModel.make(3, TapVariant.CUTOFF, WinVariant.MISERE_B)
    for player_id in [PlayerId(0), PlayerId(1)]:
        for hand_id in [HandId(0), HandId(1)]:
            for _ in range(3):
                model.do_tap(HandId(0), (player_id, hand_id))
    winner = model.get_winner()
    assert winner == PlayerId(1)
