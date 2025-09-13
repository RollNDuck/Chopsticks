from __future__ import annotations
from typing import NewType, Protocol
from enum import StrEnum


PlayerId = NewType('PlayerId', int)
HandId = NewType('HandId', int)


class TapVariant(StrEnum):
    CUTOFF = 'Cutoff'
    ROLLOVER = 'Rollover'


class WinVariant(StrEnum):
    STANDARD = 'Standard'
    MISERE_A = 'Misere A'
    MISERE_B = 'Misere B'


class Action(StrEnum):
    TAP = 'Tap'
    SPLIT = 'Split'


class HandInfo(Protocol):
    @property
    def hand_id(self) -> HandId: ...

    @property
    def player_id(self) -> PlayerId: ...

    @property
    def fingers_up(self) -> int: ...

    @property
    def total_fingers(self) -> int: ...

    def is_active(self) -> bool: ...

    def is_inactive(self) -> bool: ...

    def to(self, fingers_up: int) -> HandInfo | None: ...
