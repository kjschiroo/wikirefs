import mwapi
import mwparserfromhell as mwp
import argparse
import sys
import csv
import itertools
import logging
from .bibliography import Bibliography

logging.basicConfig(level=logging.WARNING)
REF_FIELDS = ['revid', 'citation']


def get_revids_from_infile(infile):
    for line in infile:
        yield int(line)


def group(n, iterable):
    it = iter(iterable)
    while True:
        chunk = tuple(itertools.islice(it, n))
        if not chunk:
            return
        yield chunk


def get_text_for_revisions(revids):
    chunk_size = 50
    for revid_chunk in group(chunk_size, revids):
        i = 0
        while True:
            try:
                yield from _try_get_text_for_revisions(revid_chunk)
                break
            except ConnectionError as e:
                if i > 5:
                    raise e
                else:
                    i += 1
                    continue


def _try_get_text_for_revisions(revids):
    session = mwapi.Session(
        'https://en.wikipedia.org',
        user_agent='Wiki_Ed'
    )
    results = session.get(
        action='query',
        prop='revisions',
        rvprop=['content', 'ids'],
        revids=revids
    )
    for page in results['query']['pages'].values():
        for rev in page['revisions']:
            if '*' in rev:
                yield {'revid': rev['revid'], 'text': rev['*']}
            else:
                yield {'revid': rev['revid'], 'text': ''}


def get_refs_for_revs_from_wikitext(revisions):
    refs_found = []
    for rev in revisions:
        wikicode = mwp.parse(rev['text'])
        b = Bibliography(wikicode)
        logging.warning(rev['revid'])
        refs = b.refs()
        for r in refs:
            yield from [{'revid': rev['revid'],
                        'citation': r['ref']}] * r['count']


def _get_ref_tag_refs_from_single_wikicode(wikicode):
    tags = wikicode.filter_tags()
    for t in tags:
        logging.debug(t.tag)
        if ('ref' == t.tag.lower() and
                t.contents is not None):
            yield str(t.contents).strip()


def _get_cite_template_refs_from_single_wikicode(wikicode):
    templates = wikicode.filter_templates()
    for t in templates:
        logging.debug(t.name)
        if ('cite' == t.name.lower().split()[0] or
                'citation' in t.name.lower()):
            yield str(t).strip()


def dump_refs_to(outfile, refs):
    writer = csv.DictWriter(outfile, REF_FIELDS)
    writer.writeheader()
    writer.writerows(refs)


def gather_refs_in_revs_in_stream_and_dump_to(infile, outfile):
    revids = get_revids_from_infile(infile)
    revisions = get_text_for_revisions(revids)
    refs = get_refs_for_revs_from_wikitext(revisions)
    dump_refs_to(outfile, refs)


def main():
    parser = argparse.ArgumentParser(
                        description=("Pull out reference tags "
                                     "from provided wikitext"))
    parser.add_argument('-i',
                        '--infile',
                        nargs='?',
                        type=argparse.FileType('r'),
                        default=sys.stdin)
    parser.add_argument('-o',
                        '--outfile',
                        nargs='?',
                        type=argparse.FileType('w'),
                        default=sys.stdout)
    args = parser.parse_args()
    gather_refs_in_revs_in_stream_and_dump_to(args.infile,
                                              args.outfile)


if __name__ == "__main__":
    main()
