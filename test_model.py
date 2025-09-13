import pytest
from model import ChopsticksModel
from required_types import PlayerId, HandId, TapVariant, WinVariant
from hand_info import HandInfoImpl


class TestChopsticksModel:
    def test_init_and_properties(self):
        """Test initialization and basic properties."""
        model = ChopsticksModel.make(2, TapVariant.CUTOFF, WinVariant.STANDARD)
        assert model.current_player_id == PlayerId(1)
        assert len(model.get_player_hands(PlayerId(1))) == 2
        assert model.get_player_hands(PlayerId(99)) == []
        assert model.get_winner() is None

    def test_tap_cutoff_rollover(self):
        """Test both tap variants."""
        # Cutoff: 4+2=6 -> becomes inactive (5)
        model = ChopsticksModel.make(2, TapVariant.CUTOFF, WinVariant.STANDARD)
        model.hands[PlayerId(1)][0] = HandInfoImpl(HandId(1), PlayerId(1), 4)
        model.hands[PlayerId(2)][0] = HandInfoImpl(HandId(1), PlayerId(2), 2)
        assert model.do_tap(HandId(1), (PlayerId(2), HandId(1)))
        assert model.get_player_hands(PlayerId(2))[0].is_inactive()
        
        # Rollover: 3+3=6 -> 1 finger
        model = ChopsticksModel.make(2, TapVariant.ROLLOVER, WinVariant.STANDARD)
        model.hands[PlayerId(1)][0] = HandInfoImpl(HandId(1), PlayerId(1), 3)
        model.hands[PlayerId(2)][0] = HandInfoImpl(HandId(1), PlayerId(2), 3)
        assert model.do_tap(HandId(1), (PlayerId(2), HandId(1)))
        assert model.get_player_hands(PlayerId(2))[0].fingers_up == 1

    def test_tap_rollover_exact_multiple(self):
        """Test rollover when result is exact multiple of total_fingers."""
        model = ChopsticksModel.make(2, TapVariant.ROLLOVER, WinVariant.STANDARD)
        model.hands[PlayerId(1)][0] = HandInfoImpl(HandId(1), PlayerId(1), 2)
        model.hands[PlayerId(2)][0] = HandInfoImpl(HandId(1), PlayerId(2), 3)
        assert model.do_tap(HandId(1), (PlayerId(2), HandId(1)))  # 2+3=5, should become inactive
        assert model.get_player_hands(PlayerId(2))[0].is_inactive()

    def test_invalid_taps(self):
        """Test invalid tap scenarios."""
        model = ChopsticksModel.make(2, TapVariant.CUTOFF, WinVariant.STANDARD)
        assert not model.do_tap(HandId(99), (PlayerId(2), HandId(1)))  # Invalid source
        assert not model.do_tap(HandId(1), (PlayerId(99), HandId(1)))  # Invalid target player
        assert not model.do_tap(HandId(1), (PlayerId(2), HandId(99)))  # Invalid target hand
        
        model.hands[PlayerId(1)][0] = HandInfoImpl(HandId(1), PlayerId(1), 5)  # Inactive source
        assert not model.do_tap(HandId(1), (PlayerId(2), HandId(1)))

    def test_split_operations(self):
        """Test split operations."""
        model = ChopsticksModel.make(2, TapVariant.CUTOFF, WinVariant.STANDARD)
        model.hands[PlayerId(1)][0] = HandInfoImpl(HandId(1), PlayerId(1), 3)
        model.hands[PlayerId(1)][1] = HandInfoImpl(HandId(2), PlayerId(1), 1)
        
        # Valid split
        assert model.do_split(HandId(1), HandId(2), 1)
        hands = model.get_player_hands(PlayerId(1))
        assert hands[0].fingers_up == 2 and hands[1].fingers_up == 2

    def test_invalid_splits(self):
        """Test invalid split scenarios."""
        model = ChopsticksModel.make(2, TapVariant.CUTOFF, WinVariant.STANDARD)
        assert not model.do_split(HandId(99), HandId(2), 1)  # Invalid source
        assert not model.do_split(HandId(1), HandId(99), 1)  # Invalid target
        assert not model.do_split(HandId(1), HandId(2), 0)   # Invalid transfer amount
        assert not model.do_split(HandId(1), HandId(2), 1)   # Would make source 0
        
        model.hands[PlayerId(1)][1] = HandInfoImpl(HandId(2), PlayerId(1), 4)
        assert not model.do_split(HandId(1), HandId(2), 1)   # Would make target inactive

    def test_get_sources_targets(self):
        """Test getting valid sources and targets."""
        model = ChopsticksModel.make(3, TapVariant.CUTOFF, WinVariant.STANDARD)
        
        # Tap sources/targets
        assert len(model.get_tap_sources()) == 2
        targets = model.get_tap_targets()
        assert len(targets) == 4  # 2 other players × 2 hands each
        assert targets[0].player_id == PlayerId(2)  # Sorted by player_id
        
        # Split sources/targets
        model.hands[PlayerId(1)][0] = HandInfoImpl(HandId(1), PlayerId(1), 3)
        sources = model.get_split_sources()
        assert len(sources) == 1  # Only hand with >1 finger
        
        split_targets = model.get_split_targets(HandId(1))
        assert len(split_targets) == 1
        assert model.get_split_targets(HandId(99)) == []  # Invalid source

    def test_win_conditions(self):
        """Test all win variants."""
        # Standard: last active player wins
        model = ChopsticksModel.make(2, TapVariant.CUTOFF, WinVariant.STANDARD)
        model.hands[PlayerId(2)][0] = HandInfoImpl(HandId(1), PlayerId(2), 5)
        model.hands[PlayerId(2)][1] = HandInfoImpl(HandId(2), PlayerId(2), 5)
        model._update_elimination(PlayerId(2))
        assert model.get_winner() == PlayerId(1)
        
        # Misère A: first eliminated wins
        model = ChopsticksModel.make(2, TapVariant.CUTOFF, WinVariant.MISERE_A)
        model.elim_order.append(PlayerId(1))
        assert model.get_winner() == PlayerId(1)
        
        # Misère B: last eliminated before final wins
        model = ChopsticksModel.make(3, TapVariant.CUTOFF, WinVariant.MISERE_B)
        model.elim_order = [PlayerId(1), PlayerId(2)]
        for pid in [PlayerId(1), PlayerId(2)]:
            model.hands[pid][0] = HandInfoImpl(HandId(1), pid, 5)
            model.hands[pid][1] = HandInfoImpl(HandId(2), pid, 5)
        assert model.get_winner() == PlayerId(2)

    def test_player_advancement(self):
        """Test player turn advancement and skipping inactive players."""
        model = ChopsticksModel.make(3, TapVariant.CUTOFF, WinVariant.STANDARD)
        
        # Normal advancement
        model.do_tap(HandId(1), (PlayerId(2), HandId(1)))
        assert model.current_player_id == PlayerId(2)
        
        # Skip inactive player
        model.hands[PlayerId(2)][0] = HandInfoImpl(HandId(1), PlayerId(2), 5)
        model.hands[PlayerId(2)][1] = HandInfoImpl(HandId(2), PlayerId(2), 5)
        model.current = PlayerId(2)
        assert model.current_player_id == PlayerId(3)  # Should skip to P3

    def test_internal_methods(self):
        """Test internal helper methods for coverage."""
        model = ChopsticksModel.make(2, TapVariant.CUTOFF, WinVariant.STANDARD)
        
        # _find_hand
        assert model._find_hand(PlayerId(99), HandId(1)) is None
        assert model._find_hand(PlayerId(1), HandId(99)) is None
        
        # _update_elimination (no double-add)
        model.hands[PlayerId(1)][0] = HandInfoImpl(HandId(1), PlayerId(1), 5)
        model.hands[PlayerId(1)][1] = HandInfoImpl(HandId(2), PlayerId(1), 5)
        model._update_elimination(PlayerId(1))
        model._update_elimination(PlayerId(1))
        assert len(model.elim_order) == 1
