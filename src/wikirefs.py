import mwapi
import mwparserfromhell as mwp
import argparse
import sys
import csv
import itertools
import logging

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
            yield {'revid': rev['revid'], 'text': rev['*']}


def get_refs_for_revs_from_wikitext(revisions):
    for rev in revisions:
        templates = mwp.parse(rev['text']).filter_templates()
        for t in templates:
            logging.debug(t.name)
            if 'cite' == t.name.split()[0]:
                yield {'revid': rev['revid'],
                       'citation': str(t)}


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
