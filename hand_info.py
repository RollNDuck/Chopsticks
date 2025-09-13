"""Concrete implementation of HandInfo protocol."""
from dataclasses import dataclass, field
from typing import cast
from required_types import HandId, PlayerId, HandInfo

@dataclass(frozen=True)
class HandInfoImpl:
    """Implementation of HandInfo with structural equality.
    
    Inactive hands are represented with fingers_up == total_fingers (all fingers up).
    This is consistent with the chopsticks rule that a hand with all fingers raised
    is considered inactive.
    """
    hand_id: HandId
    player_id: PlayerId
    fingers_up: int
    total_fingers: int = field(default=5, init=False)
    
    def is_active(self) -> bool:
        """Check if hand is still active.
        
        A hand is active when 0 < fingers_up < total_fingers.
        Hands with 0 fingers or all fingers up are inactive.
        """
        return 0 < self.fingers_up < self.total_fingers
    
    def is_inactive(self) -> bool:
        """Check if hand is inactive."""
        return not self.is_active()
    
    def to(self, fingers_up: int) -> HandInfo | None:
        """Create new HandInfo with specified fingers up, or None if invalid.
        
        Returns None if fingers_up is <= 0 or > total_fingers.
        Note: fingers_up == total_fingers creates an inactive hand.
        """
        if fingers_up <= 0 or fingers_up > self.total_fingers:
            return None
        return cast(HandInfo, HandInfoImpl(self.hand_id, self.player_id, fingers_up))
