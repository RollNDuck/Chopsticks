from __future__ import annotations
from typing import List, Dict
from required_types import PlayerId, HandId, HandInfo, TapVariant, WinVariant
from hand_info import HandInfoImpl


class ChopsticksModel:
    """Chopsticks model for configurable variants."""
    def __init__(self, n: int, tap_variant: TapVariant, win_variant: WinVariant):
        """Initialize model with n players and variants (1-based IDs)."""
        self.n = n
        self.tap_variant = tap_variant
        self.win_variant = win_variant
        self.current = PlayerId(1)  # 1-based indexing
        self.hands: Dict[PlayerId, List[HandInfo]] = {}
        self.elim_order: List[PlayerId] = []  # Track elimination order for MISERE variants

        # Initialize players 1 to n with hands 1 and 2
        for i in range(1, n + 1):
            player_id = PlayerId(i)
            self.hands[player_id] = [
                HandInfoImpl(HandId(1), player_id, 1),
                HandInfoImpl(HandId(2), player_id, 1)
            ]

    # --- Internal helpers -------------------------------------------------
    def _find_hand(self, player_id: PlayerId, hand_id: HandId) -> HandInfo | None:
        """Return the HandInfo for (player_id, hand_id) or None."""
        if player_id not in self.hands:
            return None
        return next((h for h in self.hands[player_id] if h.hand_id == hand_id), None)

    def _replace_player_hand(self, player_id: PlayerId, hand_id: HandId, new_hand: HandInfo) -> None:
        """Replace a player's hand immutably."""
        self.hands[player_id] = [new_hand if h.hand_id == hand_id else h for h in self.hands[player_id]]

    def _update_elimination(self, player_id: PlayerId) -> None:
        """Append player to elim_order if eliminated."""
        if player_id in self.elim_order:
            return
        player_hands = self.get_player_hands(player_id)
        if player_hands and all(h.is_inactive() for h in player_hands):
            self.elim_order.append(player_id)

    def _ensure_current_active(self) -> None:
        """Advance if current player is inactive."""
        player_hands = self.get_player_hands(self.current)
        if not player_hands or not any(h.is_active() for h in player_hands):
            self._next_player()

    @property
    def current_player_id(self) -> PlayerId:
        """Return the current active player's ID."""
        self._ensure_current_active()
        return self.current

    def get_player_hands(self, player_id: PlayerId) -> List[HandInfo]:
        """Return sorted HandInfo list for player_id, or [] if absent."""
        if player_id not in self.hands:
            return []
        return sorted([h for h in self.hands[player_id]], key=lambda h: int(h.hand_id))

    def get_hands_all_players(self) -> Dict[PlayerId, List[HandInfo]]:
        """Return hands for all players in ascending PlayerId order."""
        return {pid: self.get_player_hands(pid) for pid in sorted(self.hands.keys(), key=int)}

    def get_winner(self) -> PlayerId | None:
        """Return the winner PlayerId or None."""
        active_players = [pid for pid in sorted(self.hands.keys(), key=int)
                         if any(h.is_active() for h in self.hands[pid])]

        match self.win_variant:
            case WinVariant.STANDARD:
                return active_players[0] if len(active_players) == 1 else None
            case WinVariant.MISERE_A:
                return self.elim_order[0] if self.elim_order else None
            case WinVariant.MISERE_B:
                if len(active_players) == 1 and self.elim_order:
                    return self.elim_order[-1]
                return None

    def get_split_sources(self) -> List[HandInfo]:
        """Return valid split source hands for current player."""
        return [h for h in self.get_player_hands(self.current_player_id) if h.is_active() and h.fingers_up > 1]

    def get_split_targets(self, source: HandId) -> List[HandInfo]:
        """Return valid split target hands for the given source."""
        source_hand = self._find_hand(self.current_player_id, source)
        if source_hand is None or not source_hand.is_active() or source_hand.fingers_up <= 1:
            return []
        return [h for h in self.get_player_hands(self.current_player_id)
                if h.hand_id != source and h.is_active() and h.fingers_up + 1 < h.total_fingers]

    def get_tap_sources(self) -> List[HandInfo]:
        """Return valid tap source hands for current player."""
        return [h for h in self.get_player_hands(self.current_player_id) if h.is_active()]

    def get_tap_targets(self) -> List[HandInfo]:
        """Return valid tap targets from opponents in (player, hand) order."""
        targets: List[HandInfo] = []
        for pid in sorted(self.hands.keys(), key=int):
            if pid != self.current_player_id:
                targets.extend([h for h in self.get_player_hands(pid) if h.is_active()])
        return sorted(targets, key=lambda h: (int(h.player_id), int(h.hand_id)))

    def do_tap(self, source: HandId, target: tuple[PlayerId, HandId]) -> bool:
        """Attempt a tap; return True and advance turn if valid, else False."""
        source_hand = self._find_hand(self.current_player_id, source)
        if source_hand is None or not source_hand.is_active():
            return False

        target_player, target_hand_id = target
        target_hand = self._find_hand(target_player, target_hand_id)
        if target_hand is None or not target_hand.is_active():
            return False

        new_fingers = target_hand.fingers_up + source_hand.fingers_up

        if new_fingers >= target_hand.total_fingers:
            match self.tap_variant:
                case TapVariant.CUTOFF:
                    new_fingers = target_hand.total_fingers
                case TapVariant.ROLLOVER:
                    new_fingers = new_fingers % target_hand.total_fingers
                    if new_fingers == 0:
                        new_fingers = target_hand.total_fingers

        new_target_hand = target_hand.to(new_fingers)
        if new_target_hand is None:
            return False

        self._replace_player_hand(target_player, target_hand_id, new_target_hand)
        self._update_elimination(target_player)
        self._next_player()
        return True

    def do_split(self, source: HandId, target: HandId, to_transfer: int) -> bool:
        """Attempt a split; return True and advance turn if valid, else False."""
        source_hand = self._find_hand(self.current_player_id, source)
        target_hand = self._find_hand(self.current_player_id, target)

        if (source_hand is None or target_hand is None or
            not source_hand.is_active() or not target_hand.is_active() or
            to_transfer <= 0 or
            source_hand.fingers_up <= to_transfer or
            target_hand.fingers_up + to_transfer >= target_hand.total_fingers):
            return False

        new_source_fingers = source_hand.fingers_up - to_transfer
        new_target_fingers = target_hand.fingers_up + to_transfer

        new_source_hand = source_hand.to(new_source_fingers)
        new_target_hand = target_hand.to(new_target_fingers)

        if new_source_hand is None or new_target_hand is None:
            return False

        self._replace_player_hand(self.current_player_id, source, new_source_hand)
        self._replace_player_hand(self.current_player_id, target, new_target_hand)
        self._update_elimination(self.current_player_id)
        self._next_player()
        return True

    def _next_player(self) -> None:
        """Advance to the next active player or leave unchanged if none."""
        original_current = int(self.current)
        players_checked = 0

        while players_checked < self.n:
            next_player_int = (int(self.current) % self.n) + 1
            self.current = PlayerId(next_player_int)
            players_checked += 1

            player_hands = self.get_player_hands(self.current)
            if any(h.is_active() for h in player_hands):
                return

        self.current = PlayerId(original_current)

    @classmethod
    def make(cls, n: int, tap_variant: TapVariant, win_variant: WinVariant) -> ChopsticksModel:
        """Create a new ChopsticksModel instance."""
        return cls(n, tap_variant, win_variant)
