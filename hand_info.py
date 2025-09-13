# hand_info.py
"""Concrete implementation of HandInfo protocol."""
from dataclasses import dataclass, field
from typing import cast
from required_types import HandId, PlayerId, HandInfo

@dataclass(frozen=True)
class HandInfoImpl:
    """Implementation of HandInfo with structural equality."""
    _hand_id: HandId
    _player_id: PlayerId
    _fingers_up: int
    _total_fingers: int = field(default=5, init=False)
    
    @property
    def hand_id(self) -> HandId:
        """Return the hand identifier."""
        return self._hand_id
    
    @property
    def player_id(self) -> PlayerId:
        """Return the player identifier."""
        return self._player_id
    
    @property
    def fingers_up(self) -> int:
        """Return number of fingers currently up."""
        return self._fingers_up
    
    @property
    def total_fingers(self) -> int:
        """Return total number of fingers on hand."""
        return self._total_fingers
    
    def is_active(self) -> bool:
        """Check if hand is still active."""
        return 0 < self._fingers_up < self._total_fingers
    
    def is_inactive(self) -> bool:
        """Check if hand is inactive."""
        return not self.is_active()
    
    def to(self, fingers_up: int) -> HandInfo | None:
        """Create new HandInfo with specified fingers up, or None if invalid."""
        if fingers_up <= 0 or fingers_up > self._total_fingers:
            return None
        return HandInfoImpl(self._hand_id, self._player_id, fingers_up)
