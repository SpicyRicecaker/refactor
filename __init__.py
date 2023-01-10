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



class Program:
    def __init__(self):
        self.stemmer = snowballstemmer.stemmer("english")
        self.re_invalid_char = re.compile(r"[\(\\\)\[\]]")
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
    def process(self, word: str, ex: str) -> str:
        stem: str = self.stemmer.stemWord(word)
        # ensure our stem actually has a valid form
        if self.re_invalid_char.search(stem):
            return

        # first try to stem everything
        words = ex.split()
        words_stemmed: list[str] = self.stemmer.stemWords(words)

        # find the index in which stem matches word
        
        # a full word is in the form ab
        try: 
            # may fail if the word isn't in there
            w_ex = words[words_stemmed.index(stem)]
            w_long, w_short = (lambda : (w_ex, stem) if len(w_ex) > len(stem) else (stem, w_ex))()

            buf_a = ""

            idx = 0
            for i in range(len(w_short)):
                if w_long[i] != w_short[i]:
                    break
                else:
                    buf_a += w_long[i]
                    idx += 1

            buf_b = w_long[idx:]

            replacement = "{{c1::" + buf_a + "}}" + buf_b

            return ex.replace(w_ex, replacement)
        except:
            return None
        
    def run(self):
        u_count = 0
        # get the **currently selected deck**
        d = mw.col.decks.current()
        d_name = d.get("name")

        # for each **basic note** in selected deck, traverse **every field**
        model_cloze = mw.col.models.id_for_name("Cloze")

        for id in mw.col.find_notes(f"deck:{d_name} AND note:basic"):
            note = mw.col.get_note(id)

            word, pronoun, ex = Program.sift_substrates(note.fields[1])

            if not ex:
                continue

            # we currently have word, pronoun, ex, and stem
            ex = self.process(word, ex)

            if not ex:
                continue

            print(ex)
            print("--------------------------")

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

def main():
    program = Program()
    program.run()

# # create a new menu item, "refactor"
action = QAction("Refactor", mw)
# set it to call testFunction when it's clicked
qconnect(action.triggered, main)
# and add it to the tools menu
mw.form.menuTools.addAction(action)


def test(back: str):
    program = Program()
    word, pronoun, ex = Program.sift_substrates(back)
    
    if not ex:
        return

    # we currently have word, pronoun, ex, and stem
    ex = program.process(word, ex)

    if not ex:
        return

    print(f"{word}  {pronoun}  {ex}")
    
# create a new menu item, test
action_t = QAction("Test", mw)
qconnect(
    action_t.triggered,
    lambda : test("brace<br><br>Glancing over, he saw Tasukete had lowered his posture and was bracing himself. If he’d been carrying a weapon, Tasukete would likely have drawn it like Haruhiro had.")
)
mw.form.menuTools.addAction(action_t)
