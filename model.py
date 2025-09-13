# model.py
"""Model implementation for Chopsticks game."""
from __future__ import annotations
from typing import List, Dict
from required_types import *
from hand_info import HandInfoImpl

class ChopsticksModel:
    """Game model for configurable Chopsticks with variants."""

    def __init__(self, n: int, tap_variant: TapVariant, win_variant: WinVariant):
        """Initialize game with n players and specified variants."""
        self.n = n
        self.tap_variant = tap_variant
        self.win_variant = win_variant
        self.current = PlayerId(0)
        self.hands: Dict[PlayerId, List[HandInfoImpl]] = {}

        for i in range(n):
            player_id = PlayerId(i)
            self.hands[player_id] = [
                HandInfoImpl(HandId(0), player_id, 1),
                HandInfoImpl(HandId(1), player_id, 1)
            ]

    @property
    def current_player_id(self) -> PlayerId:
        """Get current player's ID."""
        return PlayerId(self.current)

    def get_player_hands(self, player_id: PlayerId) -> List[HandInfo]:
        """Get sorted list of hands for specified player."""
        return sorted([h for h in self.hands[player_id]], key=lambda h: h.hand_id)

    def get_hands_all_players(self) -> Dict[PlayerId, List[HandInfo]]:
        """Get hands for all players."""
        return {pid: self.get_player_hands(pid) for pid in self.hands.keys()}

    def get_winner(self) -> PlayerId | None:
        """Determine winner based on current win variant."""
        active_players = [pid for pid, hands in self.hands.items()
                         if any(h.is_active() for h in hands)]

        match self.win_variant:
            case WinVariant.STANDARD:
                return active_players[0] if len(active_players) == 1 else None
            case WinVariant.MISERE_A:
                out_players = [pid for pid in self.hands.keys() if pid not in active_players]
                return out_players[0] if out_players else None
            case WinVariant.MISERE_B:
                if len(active_players) == 1:
                    out_players = [pid for pid in self.hands.keys() if pid not in active_players]
                    return out_players[-1] if out_players else None
                return None

    def get_split_sources(self) -> List[HandInfo]:
        """Get valid split source hands for current player."""
        return [h for h in self.get_player_hands(self.current_player_id)
                if h.is_active() and h.fingers_up > 1]

    def get_split_targets(self, source: HandId) -> List[HandInfo]:
        """Get valid split target hands for given source."""
        source_hand = next(h for h in self.get_player_hands(self.current_player_id)
                          if h.hand_id == source)
        return [h for h in self.get_player_hands(self.current_player_id)
                if h.hand_id != source and h.is_active() and
                h.fingers_up + 1 < h.total_fingers and
                source_hand.fingers_up > 1]

    def get_tap_sources(self) -> List[HandInfo]:
        """Get valid tap source hands for current player."""
        return [h for h in self.get_player_hands(self.current_player_id) if h.is_active()]

    def get_tap_targets(self) -> List[HandInfo]:
        """Get valid tap target hands from opponents."""
        targets = []
        for pid in sorted(self.hands.keys()):
            if pid != self.current_player_id:
                targets.extend([h for h in self.get_player_hands(pid) if h.is_active()])
        return sorted(targets, key=lambda h: (h.player_id, h.hand_id))

    def do_tap(self, source: HandId, target: tuple[PlayerId, HandId]) -> bool:
        """Perform tap action from source to target hand."""
        source_hand = next(h for h in self.get_player_hands(self.current_player_id)
                          if h.hand_id == source)
        target_player, target_hand_id = target
        target_hand = next(h for h in self.get_player_hands(target_player)
                          if h.hand_id == target_hand_id)

        if not source_hand.is_active() or not target_hand.is_active():
            return False

        new_fingers = target_hand.fingers_up + source_hand.fingers_up

        if new_fingers == target_hand.total_fingers:
            new_fingers = 0
        elif new_fingers > target_hand.total_fingers:
            match self.tap_variant:
                case TapVariant.CUTOFF:
                    new_fingers = 0
                case TapVariant.ROLLOVER:
                    new_fingers -= target_hand.total_fingers

        new_target_hand = target_hand.to(new_fingers)
        if new_target_hand is None:
            return False

        self.hands[target_player] = [
            new_target_hand if h.hand_id == target_hand_id else h
            for h in self.get_player_hands(target_player)
        ]
        self._next_player()
        return True

    def do_split(self, source: HandId, target: HandId, to_transfer: int) -> bool:
        """Perform split action transferring fingers from source to target."""
        source_hand = next(h for h in self.get_player_hands(self.current_player_id)
                          if h.hand_id == source)
        target_hand = next(h for h in self.get_player_hands(self.current_player_id)
                          if h.hand_id == target)

        if (not source_hand.is_active() or not target_hand.is_active() or
            to_transfer <= 0 or source_hand.fingers_up <= to_transfer or
            target_hand.fingers_up + to_transfer >= target_hand.total_fingers):
            return False

        new_source_fingers = source_hand.fingers_up - to_transfer
        new_target_fingers = target_hand.fingers_up + to_transfer

        new_source_hand = source_hand.to(new_source_fingers)
        new_target_hand = target_hand.to(new_target_fingers)

        if new_source_hand is None or new_target_hand is None:
            return False

        self.hands[self.current_player_id] = [
            new_source_hand if h.hand_id == source else
            new_target_hand if h.hand_id == target else h
            for h in self.get_player_hands(self.current_player_id)
        ]
        self._next_player()
        return True

    def _next_player(self) -> None:
        """Advance to next player with active hands."""
        self.current = (self.current + 1) % self.n
        while not any(h.is_active() for h in self.get_player_hands(PlayerId(self.current))):
            self.current = (self.current + 1) % self.n

    @classmethod
    def make(cls, n: int, tap_variant: TapVariant, win_variant: WinVariant) -> ChopsticksModel:
        """Create new ChopsticksModel instance."""
        return cls(n, tap_variant, win_variant)
