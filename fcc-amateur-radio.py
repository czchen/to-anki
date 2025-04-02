#!/usr/bin/env python3
import argparse
import dataclasses
import random
import re
import sys

import genanki
import pdfplumber


@dataclasses.dataclass
class Question:
    question: str = ''
    choice_a: str = ''
    choice_b: str = ''
    choice_c: str = ''
    choice_d: str = ''
    tags: list[str] = dataclasses.field(default_factory=list)
    answer: str = ''


def get_args():
    parser = argparse.ArgumentParser(description='FCC Amateur Radio Question Pool')
    parser.add_argument('--name', type=str, nargs=1, required=True, help='Name')
    parser.add_argument('--pdf', type=str, nargs=1, required=True, help='Question pool')
    parser.add_argument('--apkg', type=str, nargs=1, required=True, help='Output package name')
    return parser.parse_args()


def main():
    args = get_args()

    qs = extract_questions_from_pdf(args.pdf[0])
    print(f'Extracted {len(qs)} questions from {args.pdf[0]}')
    desk = build_anki_deck(args.name[0], qs)
    genanki.Package(desk).write_to_file(args.apkg[0])


def extract_questions_from_pdf(file):
    qs = []
    tags = {}
    q = Question()
    previous_step = None
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            for line in page.extract_text().split('\n'):
                m = re.search(r'^SUBELEMENT (?P<number>[GT]\d+) (?:[-–] )?(?P<title>.*) (?:[-–] )?\[', line)

                if m:
                    tags[m.group('number')] = (m.group('number').strip() + '-' + m.group('title').strip()).replace(' ', '_')
                    continue

                m = re.search(r'^(?P<number>[GT]\d.{3})\s*\((?P<answer>[ABCD])\)', line)
                if m:
                    q.question = m.group('number') + '.'
                    q.answer = m.group('answer')

                    t = m.group('number')[:2]
                    if t in tags:
                        q.tags.append(tags[t])

                    previous_step = 'question'
                    continue

                m = re.search(r'^A[.].*', line)
                if m:
                    q.choice_a = line.strip()
                    previous_step = 'choice_a'
                    continue

                m = re.search(r'^B[.].*', line)
                if m:
                    q.choice_b = line.strip()
                    previous_step = 'choice_b'
                    continue

                m = re.search(r'^C[.].*', line)
                if m:
                    q.choice_c = line.strip()
                    previous_step = 'choice_c'
                    continue

                m = re.search(r'^D[.].*', line)
                if m:
                    q.choice_d = line.strip()
                    previous_step = 'choice_d'
                    continue

                if line.strip() == '~~':
                    if q.answer == 'A':
                        q.answer = q.choice_a
                    elif q.answer == 'B':
                        q.answer = q.choice_b
                    elif q.answer == 'C':
                        q.answer = q.choice_c
                    elif q.answer == 'D':
                        q.answer = q.choice_d

                    qs.append(q)
                    q = Question()

                if previous_step == 'question':
                    q.question += ' ' + line.strip()
                elif previous_step == 'choice_a':
                    q.choice_a += ' ' + line.strip()
                elif previous_step == 'choice_b':
                    q.choice_b += ' ' + line.strip()
                elif previous_step == 'choice_c':
                    q.choice_c += ' ' + line.strip()
                elif previous_step == 'choice_d':
                    q.choice_d += ' ' + line.strip()
    return qs


def build_anki_deck(name,  qs):
    model = genanki.Model(
        random_id(),
        name,
        fields=[
            {'name': 'Question'},
            {'name': 'Answer'},
        ],
        templates=[
            {
                'name': 'Card 1',
                'qfmt': '{{Question}}',
                'afmt': '{{FrontSide}}<hr id="answer">{{Answer}}',
            },
        ],
    )

    desk = genanki.Deck(
        random_id(),
        name,
    )

    for q in qs:
        note = genanki.Note(
            model=model,
            fields=[
                f'{q.question}<br>{q.choice_a}<br>{q.choice_b}<br>{q.choice_c}<br>{q.choice_d}',
                q.answer,
            ],
            tags=q.tags,
        )
        desk.add_note(note)

    return desk


def random_id():
    return random.randrange(1 << 30, 1 << 31)


if __name__ == '__main__':
    sys.exit(main())
