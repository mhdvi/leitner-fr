"""Builds js/data/words.js from the Farsi translation files in tools/fa/.

Sources (downloaded into tools/.cache on first run):
  - FLELex (CEFR-graded French lexicon, CENTAL / UCLouvain, CC BY-NC-SA 4.0)
  - Lexique 3.83 (gender, plurals, feminine forms, verb forms; CC BY-SA 4.0)
  - ipa-dict French IPA (derived from Wiktionary)

Translation lines look like `word=farsi`. Two optional overrides may follow:
  `word=farsi|pos`              fix the part of speech
  `word=farsi|pos|display`      fix the displayed form (e.g. `les vacances`, `mai`)
A meaning of `-` drops the word. Nouns are shown with un / une unless overridden.

Usage:  python tools/build_words.py
"""
import csv, glob, json, os, urllib.request
from collections import defaultdict

ROOT = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(ROOT, '.cache')
OUT = os.path.join(ROOT, '..', 'js', 'data', 'words.js')

SOURCES = {
    'flelex_beacco.tsv': 'https://cental.uclouvain.be/cefrlex/static/resources/fr/FleLex_TT_Beacco.tsv',
    'lexique.tsv': 'http://www.lexique.org/databases/Lexique383/Lexique383.tsv',
    'fr_ipa.txt': 'https://raw.githubusercontent.com/open-dict-data/ipa-dict/master/data/fr_FR.txt',
}
TAGS = {'NOM': 'n', 'VER': 'v', 'ADJ': 'adj', 'ADV': 'adv', 'PRO': 'pron', 'PRP': 'prep', 'KON': 'conj', 'INT': 'excl'}
LEVELS = ['a1', 'a2', 'b1', 'b2']

# Verbs conjugated with être in the passé composé.
ETRE = set('''aller arriver descendre redescendre devenir redevenir entrer rentrer monter remonter mourir naître
renaître partir repartir rester retourner revenir sortir ressortir tomber retomber venir parvenir intervenir
survenir provenir advenir décéder'''.split())


def fetch(name):
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, name)
    if not os.path.exists(path):
        print('downloading', name)
        urllib.request.urlretrieve(SOURCES[name], path)
    return path


def main():
    translations = {}
    for f in sorted(glob.glob(os.path.join(ROOT, 'fa', '*.txt'))):
        for line in open(f, encoding='utf-8'):
            line = line.strip()
            if not line:
                continue
            key, _, rest = line.partition('=')
            parts = rest.split('|')
            if parts[0] != '-':
                translations[key] = parts

    # FLELex: level, part of speech and frequency per word.
    flelex = {}
    for x in csv.DictReader(open(fetch('flelex_beacco.tsv'), encoding='utf-8'), delimiter='\t'):
        w = x['word'].strip()
        if x['level'].lower() not in LEVELS or x['tag'] not in TAGS:
            continue
        e = flelex.setdefault(w, {'tags': defaultdict(float), 'lvl': x['level'].lower(), 'f': 0.0})
        e['tags'][TAGS[x['tag']]] += float(x['freq_total'])
        e['lvl'] = min(e['lvl'], x['level'].lower())
        e['f'] = max(e['f'], float(x['freq_total']))
    for e in flelex.values():
        e['pos'] = sorted(e['tags'], key=e['tags'].get, reverse=True)  # most frequent use first

    # Lexique: gender, plural, feminine and verb forms, picking the most frequent form.
    gender = defaultdict(lambda: defaultdict(float))
    best = {}

    def keep(kind, lemma, form, freq):
        k = (kind, lemma)
        if k not in best or freq > best[k][1]:
            best[k] = (form, freq)

    for x in csv.DictReader(open(fetch('lexique.tsv'), encoding='utf-8'), delimiter='\t'):
        lemma, form, cg = x['lemme'], x['ortho'], x['cgram']
        freq = float(x['freqfilms2'] or 0) + float(x['freqlivres'] or 0)
        if cg == 'NOM':
            if x['genre'] in ('m', 'f'):
                gender[lemma][x['genre']] += freq + 0.01
            if x['nombre'] == 'p':
                keep('pl', lemma, form, freq)
        elif cg == 'ADJ' and x['genre'] == 'f' and x['nombre'] in ('s', ''):
            keep('fem', lemma, form, freq)
        elif cg == 'VER':
            info = x['infover']
            if 'ind:pre:3s' in info:
                keep('p3', lemma, form, freq)
            if 'par:pas' in info and x['genre'] in ('m', '') and x['nombre'] in ('s', ''):
                keep('pp', lemma, form, freq)

    ipa = {}
    for line in open(fetch('fr_ipa.txt'), encoding='utf-8'):
        k, _, v = line.rstrip('\n').partition('\t')
        if k not in ipa:
            ipa[k] = v.split(',')[0].strip().strip('/')

    def spell(w):
        # FLELex writes the ligature œ as "oe" (oeil, coeur); restore it where the dictionary knows it.
        alt = w.replace('oe', 'œ')
        return alt if alt != w and alt in ipa else w

    rows, missing = [], []
    for word, parts in translations.items():
        e = flelex.get(word)
        if not e:
            missing.append(word)
            continue
        fa = parts[0]
        pos = parts[1] if len(parts) > 1 and parts[1] else e['pos'][0]
        g = ''
        if pos == 'n':
            gg = gender.get(word) or {}
            g = max(gg, key=gg.get) if gg else ''
        if len(parts) > 2:
            display = parts[2]
            first = display.split(' ')[0]
            g = {'un': 'm', 'le': 'm', 'une': 'f', 'la': 'f'}.get(first, g if first.startswith("l'") else '')
        elif pos == 'n' and g:
            display = ('un ' if g == 'm' else 'une ') + spell(word)
        else:
            display = spell(word)
        lemma = display.split(' ', 1)[1] if ' ' in display and display.split(' ')[0] in ('un', 'une', 'le', 'la', 'les') else display
        lemma = lemma[2:] if lemma.startswith("l'") else lemma

        extra = ''
        if pos == 'n' and len(parts) < 3:
            pl = best.get(('pl', word), ('', 0))[0]
            if pl and pl not in (word, word + 's') and not (word[-1] in 'sxz' and pl == word):
                extra = pl
        elif pos == 'adj':
            fem = best.get(('fem', word), ('', 0))[0]
            if fem and fem != word:
                extra = fem
        elif pos == 'v':
            p3 = best.get(('p3', word), ('', 0))[0]
            pp = best.get(('pp', word), ('', 0))[0]
            if p3 and pp:
                aux = 'est' if word in ETRE else 'a'
                extra = f'il {p3} · il {aux} {pp}'
        rows.append((LEVELS.index(e['lvl']), -e['f'], [display, fa, ipa.get(lemma) or ipa.get(spell(word)) or ipa.get(word, ''), pos, e['lvl'], extra, g]))

    if missing:
        raise SystemExit(f'unknown words in translations: {missing[:20]}')

    rows.sort(key=lambda r: (r[0], r[1]))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write('// Generated by tools/build_words.py. Do not edit by hand.\n')
        f.write('// [word (nouns with un/une), farsi, ipa, part of speech, level, extra, gender]\n')
        f.write('// extra: irregular plural (nouns), feminine (adjectives), "il … · il a/est …" (verbs)\n')
        f.write('export default [\n')
        for _, _, r in rows:
            f.write(json.dumps(r, ensure_ascii=False, separators=(',', ':')) + ',\n')
        f.write('];\n')
    counts = {l: sum(1 for r in rows if r[2][4] == l) for l in LEVELS}
    no_ipa = sum(1 for r in rows if not r[2][2])
    print(f'{len(rows)} words written to {os.path.relpath(OUT)}', counts, f'without IPA: {no_ipa}')


if __name__ == '__main__':
    main()
