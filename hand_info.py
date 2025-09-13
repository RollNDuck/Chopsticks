# hand_info.py
"""Concrete implementation of HandInfo protocol."""
from dataclasses import dataclass
from required_types import HandId, PlayerId, HandInfo

@dataclass(frozen=True)
class HandInfoImpl:
    """Implementation of HandInfo with structural equality."""
    hand_id: HandId
    player_id: PlayerId
    fingers_up: int
    total_fingers: int = 5

    @property
    def hand_id(self) -> HandId:
        """Return the hand identifier."""
        return self.hand_id

    @property
    def player_id(self) -> PlayerId:
        """Return the player identifier."""
        return self.player_id

    @property
    def fingers_up(self) -> int:
        """Return number of fingers currently up."""
        return self.fingers_up

    @property
    def total_fingers(self) -> int:
        """Return total number of fingers on hand."""
        return self.total_fingers

    def is_active(self) -> bool:
        """Check if hand is still active."""
        return 0 < self.fingers_up < self.total_fingers

    def is_inactive(self) -> bool:
        """Check if hand is inactive."""
        return not self.is_active()

    def to(self, fingers_up: int) -> HandInfo | None:
        """Create new HandInfo with specified fingers up, or None if invalid."""
        if fingers_up <= 0 or fingers_up > self.total_fingers:
            return None
        return HandInfoImpl(self.hand_id, self.player_id, fingers_up, self.total_fingers)
