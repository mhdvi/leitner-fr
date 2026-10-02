# Leitner Français (لایتنر فرانسوی)

A private, offline-first web app (PWA) for learning 6,088 French words, French → Farsi, with the five-box Leitner system. The interface is in Farsi (right-to-left) by default. It can be switched to English on the first screen or in Settings.

## Run it

It's a static site with no build step:

```sh
python tools/serve.py        # http://localhost:8000
```

## What's specific to French

- **Word bank.** Words from A1 to B2, taking the level each word first appears at in FLELex, a CEFR-graded lexicon built from French-as-a-foreign-language textbooks. Within a level, the most frequent words come first.
- **Gender.** Nouns are shown with *un* / *une*, tinted by gender, and spoken with the article.
- **Word forms** from Lexique 3:
  - nouns show their irregular plural (*des yeux*, *des chevaux*);
  - adjectives show their feminine (*beau → belle*);
  - verbs show présent + passé composé (*il va · il est allé*).
- **Pronunciation.** Uses the device's French voice (`fr-FR` preferred). Phonetics come from ipa-dict (Wiktionary).

## Your own word lists

Settings → Word lists lets you add your own words and study them in the same Leitner boxes.

- **Adding a list.** Paste words or choose a CSV/TXT file, one `word, meaning` per line. The separator can be a comma, tab, `=`, `:` or `;`; extra columns are further meanings, and an optional last column in `/slashes/` is used as the phonetics. Write nouns with their article (*le chien*, *une maison*) and they're tinted by gender like the built-in words. There's a template to download, Excel's Windows-1256 Farsi files are read correctly, and a list holds up to 5,000 words.
- **Studying.** New cards come from your enabled lists first, then from the built-in words. A word that is also in the built-in words is studied from your list, with your meaning. Quiz options for list words draw on the same list (when it has 12 or more words) and on the whole word bank.
- **Switching on and off.** The built-in words and each list have a switch (at least one stays on). A switched-off list is paused and keeps its boxes. Deleting a list removes its words and their progress. Each list can be exported as CSV.
- **Storage.** Lists are saved with your progress, so they're included in the backup file. Resetting progress keeps your lists.

## Data and licences

- **FLELex**, CENTAL / UCLouvain: CC BY-NC-SA 4.0. Because of the non-commercial and share-alike terms, this app should stay free and non-commercial. Keep the attribution shown in Settings → About.
- **Lexique 3.83**, New & Pallier: CC BY-SA 4.0.
- **ipa-dict**, open-dict-data: IPA taken from Wiktionary.

## Editing the word bank

1. Edit `tools/fa/*.txt`:
   - `word=meaning` sets the Farsi meaning;
   - `word=-` drops the word;
   - `word=meaning|pos|display` sets the part of speech and/or the displayed form, e.g. `les vacances` or `mai`.
2. Run `python tools/build_words.py`. The sources download into `tools/.cache` on the first run.
3. Change `VERSION` in `sw.js` so installed copies pick up the new data.
