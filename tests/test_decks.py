from anki_activitywatch.core.decks import most_common_deck


def test_single_deck():
    assert most_common_deck(["Class::2026B::Econ::Ch03"]) == "Class::2026B::Econ::Ch03"


def test_most_common_wins():
    assert most_common_deck(["A", "B", "B", "C"]) == "B"


def test_tie_goes_to_first_sorted_name_regardless_of_order():
    assert most_common_deck(["Z", "A", "Z", "A"]) == "A"
    assert most_common_deck(["A", "Z", "A", "Z"]) == "A"


def test_none_and_empty_are_ignored():
    assert most_common_deck([None, "", "B", None, None]) == "B"
    assert most_common_deck([]) is None
    assert most_common_deck([None]) is None
