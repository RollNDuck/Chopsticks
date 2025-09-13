import pytest
from model import ChopsticksModel
from required_types import PlayerId, HandId, TapVariant, WinVariant
from hand_info import HandInfoImpl


class TestChopsticksModel:
    def test_init_and_basic_properties(self):
        """Test model initialization and basic property access."""
        model = ChopsticksModel.make(2, TapVariant.CUTOFF, WinVariant.STANDARD)
        assert model.current_player_id == PlayerId(1)
        assert len(model.get_player_hands(PlayerId(1))) == 2
        assert len(model.get_player_hands(PlayerId(2))) == 2
        assert model.get_winner() is None

    def test_get_hands_all_players(self):
        """Test getting all players' hands."""
        model = ChopsticksModel.make(3, TapVariant.CUTOFF, WinVariant.STANDARD)
        all_hands = model.get_hands_all_players()
        assert len(all_hands) == 3
        assert all(len(hands) == 2 for hands in all_hands.values())

    def test_get_player_hands_invalid_player(self):
        """Test getting hands for non-existent player."""
        model = ChopsticksModel.make(2, TapVariant.CUTOFF, WinVariant.STANDARD)
        assert model.get_player_hands(PlayerId(99)) == []

    def test_tap_cutoff_variant(self):
        """Test tapping with cutoff variant."""
        model = ChopsticksModel.make(2, TapVariant.CUTOFF, WinVariant.STANDARD)
        # Set up P1 hand 1 with 4 fingers, P2 hand 1 with 2 fingers
        model.hands[PlayerId(1)][0] = HandInfoImpl(HandId(1), PlayerId(1), 4)
        model.hands[PlayerId(2)][0] = HandInfoImpl(HandId(1), PlayerId(2), 2)

        # Tap should make P2 hand inactive (4+2=6, cutoff at 5)
        assert model.do_tap(HandId(1), (PlayerId(2), HandId(1)))
        target_hand = model.get_player_hands(PlayerId(2))[0]
        assert target_hand.is_inactive()

    def test_tap_rollover_variant(self):
        """Test tapping with rollover variant."""
        model = ChopsticksModel.make(2, TapVariant.ROLLOVER, WinVariant.STANDARD)
        # Set up P1 hand 1 with 3 fingers, P2 hand 1 with 3 fingers
        model.hands[PlayerId(1)][0] = HandInfoImpl(HandId(1), PlayerId(1), 3)
        model.hands[PlayerId(2)][0] = HandInfoImpl(HandId(1), PlayerId(2), 3)

        # Tap should rollover (3+3=6, 6%5=1)
        assert model.do_tap(HandId(1), (PlayerId(2), HandId(1)))
        target_hand = model.get_player_hands(PlayerId(2))[0]
        assert target_hand.fingers_up == 1

    def test_tap_rollover_exact_multiple(self):
        """Test rollover when result is exact multiple of total_fingers."""
        model = ChopsticksModel.make(2, TapVariant.ROLLOVER, WinVariant.STANDARD)
        # Set up for exactly 10 fingers (2*5)
        model.hands[PlayerId(1)][0] = HandInfoImpl(HandId(1), PlayerId(1), 5)
        model.hands[PlayerId(2)][0] = HandInfoImpl(HandId(1), PlayerId(2), 5)

        # Should become inactive (10 % 5 = 0, set to 5 = total_fingers)
        assert model.do_tap(HandId(1), (PlayerId(2), HandId(1)))
        target_hand = model.get_player_hands(PlayerId(2))[0]
        assert target_hand.is_inactive()

    def test_invalid_taps(self):
        """Test various invalid tap scenarios."""
        model = ChopsticksModel.make(2, TapVariant.CUTOFF, WinVariant.STANDARD)

        # Invalid source hand
        assert not model.do_tap(HandId(99), (PlayerId(2), HandId(1)))

        # Invalid target player
        assert not model.do_tap(HandId(1), (PlayerId(99), HandId(1)))

        # Invalid target hand
        assert not model.do_tap(HandId(1), (PlayerId(2), HandId(99)))

        # Inactive source hand
        model.hands[PlayerId(1)][0] = HandInfoImpl(HandId(1), PlayerId(1), 5)
        assert not model.do_tap(HandId(1), (PlayerId(2), HandId(1)))

    def test_split_valid(self):
        """Test valid split operation."""
        model = ChopsticksModel.make(2, TapVariant.CUTOFF, WinVariant.STANDARD)
        # Set up P1 hands: hand 1 with 3 fingers, hand 2 with 1 finger
        model.hands[PlayerId(1)][0] = HandInfoImpl(HandId(1), PlayerId(1), 3)
        model.hands[PlayerId(1)][1] = HandInfoImpl(HandId(2), PlayerId(1), 1)

        # Transfer 1 finger from hand 1 to hand 2
        assert model.do_split(HandId(1), HandId(2), 1)
        hands = model.get_player_hands(PlayerId(1))
        assert hands[0].fingers_up == 2  # hand 1: 3-1=2
        assert hands[1].fingers_up == 2  # hand 2: 1+1=2

    def test_split_invalid_cases(self):
        """Test invalid split scenarios."""
        model = ChopsticksModel.make(2, TapVariant.CUTOFF, WinVariant.STANDARD)

        # Invalid transfer amount
        assert not model.do_split(HandId(1), HandId(2), 0)
        assert not model.do_split(HandId(1), HandId(2), -1)

        # Transfer too many fingers (would make source inactive)
        assert not model.do_split(HandId(1), HandId(2), 1)  # 1-1=0

        # Target would become inactive
        model.hands[PlayerId(1)][1] = HandInfoImpl(HandId(2), PlayerId(1), 4)
        assert not model.do_split(HandId(1), HandId(2), 1)  # 4+1=5 (inactive)

    def test_get_split_sources_and_targets(self):
        """Test getting valid split sources and targets."""
        model = ChopsticksModel.make(2, TapVariant.CUTOFF, WinVariant.STANDARD)
        model.hands[PlayerId(1)][0] = HandInfoImpl(HandId(1), PlayerId(1), 3)
        model.hands[PlayerId(1)][1] = HandInfoImpl(HandId(2), PlayerId(1), 2)

        sources = model.get_split_sources()
        assert len(sources) == 2  # Both hands can be sources

        targets = model.get_split_targets(HandId(1))
        assert len(targets) == 1  # Only hand 2 can be target from hand 1

    def test_get_tap_sources_and_targets(self):
        """Test getting valid tap sources and targets."""
        model = ChopsticksModel.make(3, TapVariant.CUTOFF, WinVariant.STANDARD)

        sources = model.get_tap_sources()
        assert len(sources) == 2  # Current player's active hands

        targets = model.get_tap_targets()
        assert len(targets) == 4  # Other players' active hands (2 players × 2 hands)

        # Check sorting order (by player_id, then hand_id)
        assert targets[0].player_id == PlayerId(2)
        assert targets[0].hand_id == HandId(1)

    def test_standard_win_condition(self):
        """Test standard win condition."""
        model = ChopsticksModel.make(2, TapVariant.CUTOFF, WinVariant.STANDARD)

        # Eliminate player 2
        model.hands[PlayerId(2)][0] = HandInfoImpl(HandId(1), PlayerId(2), 5)
        model.hands[PlayerId(2)][1] = HandInfoImpl(HandId(2), PlayerId(2), 5)
        model._update_elimination(PlayerId(2))

        winner = model.get_winner()
        assert winner == PlayerId(1)

    def test_misere_a_win_condition(self):
        """Test Misère A win condition (first eliminated wins)."""
        model = ChopsticksModel.make(2, TapVariant.CUTOFF, WinVariant.MISERE_A)

        # Eliminate player 1 first
        model.elim_order.append(PlayerId(1))
        winner = model.get_winner()
        assert winner == PlayerId(1)

    def test_misere_b_win_condition(self):
        """Test Misère B win condition (last eliminated before final wins)."""
        model = ChopsticksModel.make(3, TapVariant.CUTOFF, WinVariant.MISERE_B)

        # Eliminate players in order: 1, 2, leaving 3
        model.elim_order = [PlayerId(1), PlayerId(2)]
        model.hands[PlayerId(1)][0] = HandInfoImpl(HandId(1), PlayerId(1), 5)
        model.hands[PlayerId(1)][1] = HandInfoImpl(HandId(2), PlayerId(1), 5)
        model.hands[PlayerId(2)][0] = HandInfoImpl(HandId(1), PlayerId(2), 5)
        model.hands[PlayerId(2)][1] = HandInfoImpl(HandId(2), PlayerId(2), 5)

        winner = model.get_winner()
        assert winner == PlayerId(2)  # Last eliminated

    def test_player_advancement(self):
        """Test player turn advancement."""
        model = ChopsticksModel.make(3, TapVariant.CUTOFF, WinVariant.STANDARD)

        # Player 1 taps, should advance to player 2
        assert model.current_player_id == PlayerId(1)
        model.do_tap(HandId(1), (PlayerId(2), HandId(1)))
        assert model.current_player_id == PlayerId(2)

    def test_inactive_player_skip(self):
        """Test skipping inactive players."""
        model = ChopsticksModel.make(3, TapVariant.CUTOFF, WinVariant.STANDARD)

        # Make player 2 inactive
        model.hands[PlayerId(2)][0] = HandInfoImpl(HandId(1), PlayerId(2), 5)
        model.hands[PlayerId(2)][1] = HandInfoImpl(HandId(2), PlayerId(2), 5)
        model.current = PlayerId(2)

        # Should skip to player 3
        current = model.current_player_id
        assert current == PlayerId(3)

    def test_edge_cases(self):
        """Test various edge cases and internal methods."""
        model = ChopsticksModel.make(2, TapVariant.CUTOFF, WinVariant.STANDARD)

        # Test with no winner yet
        assert model.get_winner() is None

        # Test _find_hand with invalid player
        assert model._find_hand(PlayerId(99), HandId(1)) is None

        # Test _find_hand with valid player but invalid hand
        assert model._find_hand(PlayerId(1), HandId(99)) is None

        # Test _update_elimination (should not double-add)
        model.hands[PlayerId(1)][0] = HandInfoImpl(HandId(1), PlayerId(1), 5)
        model.hands[PlayerId(1)][1] = HandInfoImpl(HandId(2), PlayerId(1), 5)
        model._update_elimination(PlayerId(1))
        model._update_elimination(PlayerId(1))  # Should not add again
        assert len(model.elim_order) == 1
