#!/usr/bin/env python3
import argparse
import dataclasses
import re
import sys

import pdfplumber


@dataclasses.dataclass
class Question:
    question: str = ''
    choice_a: str = ''
    choice_b: str = ''
    choice_c: str = ''
    choice_d: str = ''
    answer: str = ''
    tag: str = ''


def get_args():
    parser = argparse.ArgumentParser(description='Drone PDF Question Extractor')
    parser.add_argument('file', type=str, help='Path to the PDF file')
    return parser.parse_args()


def main():
    args = get_args()
    qs = extract_questions_from_pdf(args.file)
    print(qs)


def extract_questions_from_pdf(file):
    qs = []
    with pdfplumber.open(file) as pdf:
        t = ''
        q = Question()
        mode = 'question'
        i = 0
        for page in pdf.pages:
            text = page.extract_text()

            for line in text.split('\n'):
                if mode == 'question':
                    if line == '第一章 民用航空法及相關法規答案':
                        print('switch to answer mode')
                        mode = 'answer'
                        continue

                    m = re.match(r'第.章 (?P<tag>.*)$', line)
                    if m:
                        t = m.group('tag')
                        continue

                    m = re.match(r'(?P<choice>\(.*)$', line)
                    if m:
                        choice = m.group('choice')

                        if choice.startswith('(A)'):
                            q.choice_a = choice
                        if choice.startswith('(B)'):
                            q.choice_b = choice
                        if choice.startswith('(C)'):
                            q.choice_c = choice
                        if choice.startswith('(D)'):
                            q.choice_d = choice

                            qs.append(q)
                            q = Question()
                        continue

                    m = re.match(r'(?P<question>\d+[.].*)$', line)
                    if m:
                        q.question = m.group('question')
                        q.tag = t
                        continue

                    if len(q.question) > 0 and q.question[-1] != '？':
                        q.question += line
                        continue

                if mode == 'answer':
                    no = ''
                    for token in line.split(' '):
                        m = re.match(r'(?P<no>\d+[.])', token)
                        if m:
                            no = m.group('no')
                            continue

                        if not qs[i].question.startswith(no):
                            print(f'parsing error {i=}, {qs[i].question=} != {no=}')
                            exit(-1)

                        if token == 'A':
                            qs[i].answer = qs[i].choice_a
                            i += 1
                        elif token == 'B':
                            qs[i].answer = qs[i].choice_b
                            i += 1
                        elif token == 'C':
                            qs[i].answer = qs[i].choice_c
                            i += 1
                        elif token == 'D':
                            qs[i].answer = qs[i].choice_d
                            i += 1

    return qs


if __name__ == '__main__':
    sys.exit(main())
