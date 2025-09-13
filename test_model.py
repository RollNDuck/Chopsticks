import pytest
from model import ChopsticksModel
from required_types import PlayerId, HandId, TapVariant, WinVariant

def test_init_and_make():
    model = ChopsticksModel(3, TapVariant.CUTOFF, WinVariant.STANDARD)
    assert model.n == 3 and model.current == PlayerId(1) and len(model.hands) == 3
    model2 = ChopsticksModel.make(2, TapVariant.ROLLOVER, WinVariant.MISERE_A)
    assert model2.n == 2

def test_hand_operations():
    model = ChopsticksModel(2, TapVariant.CUTOFF, WinVariant.STANDARD)
    hands = model.get_player_hands(PlayerId(1))
    assert len(hands) == 2 and hands[0].hand_id == HandId(1)
    assert model.get_player_hands(PlayerId(99)) == []
    all_hands = model.get_hands_all_players()
    assert len(all_hands) == 2

def test_tap_cutoff_valid():
    model = ChopsticksModel(2, TapVariant.CUTOFF, WinVariant.STANDARD)
    model.hands[PlayerId(2)][0] = model.hands[PlayerId(2)][0].to(4)
    assert model.do_tap(HandId(1), (PlayerId(2), HandId(1))) == True
    assert model.get_player_hands(PlayerId(2))[0].fingers_up == 5

def test_tap_rollover():
    model = ChopsticksModel(2, TapVariant.ROLLOVER, WinVariant.STANDARD)
    model.hands[PlayerId(1)][0] = model.hands[PlayerId(1)][0].to(2)
    model.hands[PlayerId(2)][0] = model.hands[PlayerId(2)][0].to(4)
    assert model.do_tap(HandId(1), (PlayerId(2), HandId(1))) == True
    model2 = ChopsticksModel(2, TapVariant.ROLLOVER, WinVariant.STANDARD)
    model2.hands[PlayerId(1)][0] = model2.hands[PlayerId(1)][0].to(2)
    model2.hands[PlayerId(2)][0] = model2.hands[PlayerId(2)][0].to(3)
    assert model2.do_tap(HandId(1), (PlayerId(2), HandId(1))) == True

def test_tap_invalid():
    model = ChopsticksModel(2, TapVariant.CUTOFF, WinVariant.STANDARD)
    assert model.do_tap(HandId(99), (PlayerId(2), HandId(1))) == False
    assert model.do_tap(HandId(1), (PlayerId(99), HandId(1))) == False
    model.hands[PlayerId(1)][0] = model.hands[PlayerId(1)][0].to(5)
    assert model.do_tap(HandId(1), (PlayerId(2), HandId(1))) == False
    bad_hand = model.hands[PlayerId(1)][0].to(6)
    assert bad_hand is None

def test_split_operations():
    model = ChopsticksModel(2, TapVariant.CUTOFF, WinVariant.STANDARD)
    model.hands[PlayerId(1)][0] = model.hands[PlayerId(1)][0].to(3)
    assert model.do_split(HandId(1), HandId(2), 1) == True
    model2 = ChopsticksModel(2, TapVariant.CUTOFF, WinVariant.STANDARD)
    assert model2.do_split(HandId(99), HandId(2), 1) == False
    assert model2.do_split(HandId(1), HandId(99), 1) == False
    assert model2.do_split(HandId(1), HandId(2), 0) == False
    assert model2.do_split(HandId(1), HandId(2), 1) == False
    model3 = ChopsticksModel(2, TapVariant.CUTOFF, WinVariant.STANDARD)
    model3.hands[PlayerId(1)][0] = model3.hands[PlayerId(1)][0].to(3)
    bad_source = model3.hands[PlayerId(1)][0].to(0)
    bad_target = model3.hands[PlayerId(1)][1].to(6)
    assert bad_source is None and bad_target is None

def test_winners_all_variants():
    model = ChopsticksModel(2, TapVariant.CUTOFF, WinVariant.STANDARD)
    assert model.get_winner() == None
    model.hands[PlayerId(2)] = [h.to(5) for h in model.hands[PlayerId(2)]]
    assert model.get_winner() == PlayerId(1)
    model2 = ChopsticksModel(2, TapVariant.CUTOFF, WinVariant.MISERE_A)
    model2.elim_order = [PlayerId(2)]
    assert model2.get_winner() == PlayerId(2)
    model2.elim_order = []
    assert model2.get_winner() == None
    model3 = ChopsticksModel(2, TapVariant.CUTOFF, WinVariant.MISERE_B)
    model3.hands[PlayerId(2)] = [h.to(5) for h in model3.hands[PlayerId(2)]]
    model3.elim_order = [PlayerId(2)]
    assert model3.get_winner() == PlayerId(2)
    model3.elim_order = []
    assert model3.get_winner() == None

def test_current_player_and_advancement():
    model = ChopsticksModel(3, TapVariant.CUTOFF, WinVariant.STANDARD)
    model.hands[PlayerId(2)] = [h.to(5) for h in model.hands[PlayerId(2)]]
    model._update_elimination(PlayerId(2))
    model.current = PlayerId(2)
    current = model.current_player_id
    assert current != PlayerId(2)
    model2 = ChopsticksModel(1, TapVariant.CUTOFF, WinVariant.STANDARD)
    model2.hands[PlayerId(1)] = [h.to(5) for h in model2.hands[PlayerId(1)]]
    original = model2.current
    model2._next_player()
    assert model2.current == original

def test_move_validation():
    model = ChopsticksModel(2, TapVariant.CUTOFF, WinVariant.STANDARD)
    model.hands[PlayerId(1)][0] = model.hands[PlayerId(1)][0].to(3)
    assert len(model.get_split_sources()) == 1
    assert len(model.get_split_targets(HandId(1))) == 1
    assert len(model.get_tap_sources()) == 2
    assert len(model.get_tap_targets()) == 2

