"""Concrete implementation of HandInfo protocol."""
from dataclasses import dataclass, field
from typing import cast
from required_types import HandId, PlayerId, HandInfo

@dataclass(frozen=True)
class HandInfoImpl:
    """HandInfo dataclass; inactive when fingers_up == total_fingers."""
    hand_id: HandId
    player_id: PlayerId
    fingers_up: int
    total_fingers: int = field(default=5, init=False)

    def is_active(self) -> bool:
        """Return True if hand is active (0 < fingers_up < total_fingers)."""
        return 0 < self.fingers_up < self.total_fingers

    def is_inactive(self) -> bool:
        """Return True if hand is inactive."""
        return not self.is_active()

    def to(self, fingers_up: int) -> HandInfo | None:
        """Return a HandInfo with fingers_up or None if invalid."""
        if fingers_up <= 0 or fingers_up > self.total_fingers:
            return None
        return cast(HandInfo, HandInfoImpl(self.hand_id, self.player_id, fingers_up))
