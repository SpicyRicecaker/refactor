# import the main window object (mw) from aqt
from typing import Tuple
from aqt import mw

# import the "show info" tool from utils.py
from aqt.utils import showInfo, qconnect

# import all of the Qt GUI library
from aqt.qt import *
import re

sys.path.append(
    "/Users/oliver/Library/Application Support/Anki2/addons21/refactor/venv/lib/python3.11/site-packages"
)

import snowballstemmer

# types
from anki.decks import DeckDict


def debug_add(d) -> None:
    # DEBUG add  card to collection
    note = mw.col.new_note(mw.col.models.by_name("Basic"))

    note.fields[0] = "cause (something)"
    note.fields[
        1
    ] = 'occasion<br><br>“When the picture was developed you could see my peepee through the opening between the two handkerchiefs which served for a loincloth, and this too occasioned much merriment.”<br><br>School occasioned much "pain and suffering"'

    mw.col.add_note(note, d.get("id"))
    mw.col.update_note(note)


# try to find word, pronoun, and example from back field
def sift_substrates(f: str) -> Tuple[str, str, str]:
    s = f.split("<br><br>")

    if s[0].find("<br>") != -1:
        # declare doubled word
        if len(s) == 1:
            t = s[0].split("<br>")
            return t[0], t[1], None
        else:
            t = s[0].split("<br>")
            s.pop(0)

            return t[0], t[1], "<br><br>".join(s)
    else:
        # declare single word
        if len(s) == 1:
            return s[0], None, None
        else:
            return s.pop(0), None, "<br><br>".join(s)


def test(front: str, back: str) -> None:
    stemmer = snowballstemmer.stemmer("english")
    word, pronoun, ex = sift_substrates(back)
    stem: str = stemmer.stemWord(word)
    print(
        f"""
    word: {word}
    pronoun: {pronoun}
    ex: {ex}
    stem: {stem}
    """
    )


# We're going to add a menu item below. First we want to create a function to
# be called when the menu item is activated.
def update_deck() -> None:
    stemmer = snowballstemmer.stemmer("english")

    u_count = 0
    # get the **currently selected deck**
    d = mw.col.decks.current()
    d_name = d.get("name")

    # for each **basic note** in selected deck, traverse **every field**
    model_cloze = mw.col.models.id_for_name("Cloze")

    re_invalid_char = re.compile(r"[\(\\\)\[\]]")

    for id in mw.col.find_notes(f"deck:{d_name} AND note:basic"):
        note = mw.col.get_note(id)

        word, pronoun, ex = sift_substrates(note.fields[1])
        print(f"[{word}]\n[{pronoun}]\n[{ex}]\n")
        if not ex:
            continue

        stem: str = stemmer.stemWord(word)

        if re_invalid_char.search(stem):
            continue

        print(stem, end="\n")

        ex, n = re.subn(
            re.compile(f"(?i)({stem})"), lambda m: f"{{{{c1::{m[0]}}}}}", ex
        )

        if n == 0:
            # try again with the word, as sometimes the stemming adds an extra
            # character to the word, e.g. musing -> muse
            ex, n = re.subn(
                re.compile(f"(?i)({word})"), lambda m: f"{{{{c1::{m[0]}}}}}", ex
            )
            if n == 0:
                continue
        # create a new card which includes the front + brbr + paragraphs
        # (matched words replaced with fuzzy-matched word clozed), and back,
        # with paragraphs and words replaced

        note_backend = note._to_backend_note()
        note_backend.notetype_id = model_cloze
        note_backend.fields[0] = f"{note.fields[0]}<br><br>{ex}"
        note_backend.fields[1] = pronoun if pronoun else ""
        note._load_from_backend_note(note_backend)

        mw.col.update_note(note)
        # increment the number of cards to collection so we don't have to quit
        u_count += 1
    debug_add(d)
    showInfo(f"Successfully updated {u_count} cards.")


# create a new menu item, "refactor"
action = QAction("Refactor", mw)
# set it to call testFunction when it's clicked
qconnect(action.triggered, update_deck)
# and add it to the tools menu
mw.form.menuTools.addAction(action)

# create a new menu item, test
action_t = QAction("Test", mw)
qconnect(
    action_t.triggered,
    lambda: test(
        "a period of reflection or thought",
        "musing<br><br>Either dialogue-heavy scenes of political argument, philosophical musing, and characters’ self-conscious descriptions of their emotions; or lush production design and photography or musical scores to pleasure the audience’s senses: THE ENGLISH PATIENT.",
    ),
)
mw.form.menuTools.addAction(action_t)
