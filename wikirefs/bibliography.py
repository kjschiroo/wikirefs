from collections import Counter
import logging

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.ERROR)


def _tag_is_ref_tag(tag):
    return 'ref' == tag.tag.lower()


def _tag_contains_template(tag):
    return (tag.contents is not None and
            len(tag.contents.filter_templates()) > 0)


def _tag_has_name_attribute(tag):
    attr = 'name'
    if not tag.has(attr):
        attr = 'Name'
    return tag.has(attr) and (tag.get(attr).value is not None)


def _get_ref_tag_name_value(tag):
    attr = 'name'
    if not tag.has(attr):
        attr = 'Name'
    return tag.get(attr).value.strip()


def _get_ref_tag_cite_template(ref_tag):
    return _standardize_template_string(ref_tag.contents.filter_templates()[0])


def _tag_is_reusable_ref_tag(tag):
    return (_tag_is_ref_tag(tag) and
            _tag_contains_template(tag) and
            _tag_has_name_attribute(tag))


def _template_is_citation_template(tmplt):
    return ('cite' == tmplt.name.lower().split()[0] or
            'citation' in tmplt.name.lower())


def _standardize_template_string(tmplt):
    return str(tmplt).strip()


class Error(Exception):
    pass


class UnknownNameError(Error):
    pass


class Bibliography(object):

    def __init__(self, wikicode):
        self._wikicode = wikicode
        self._gather_reuse_map()

    def refs(self):
        '''
        Returns a list of references of the format
        [{'ref': reference_text, 'count': n}, ...]
        '''
        named_ref_counts = self._count_named_refs()
        reused = {}
        for name, count in named_ref_counts.items():
            try:
                full_text = self._get_full_ref_text_from_name(name)
                # Reduce by one to exclude first use
                reused[full_text] = count - 1
            except UnknownNameError as e:
                logger.warning('ref named "{0}" not found'.format(name))
                continue
        reuse_counts = Counter(reused)
        cite_tmplt_counts = self._count_all_citation_templates()
        return [{'ref': text, 'count': count}
                for text, count in (reuse_counts + cite_tmplt_counts).items()]

    def _get_full_ref_text_from_name(self, name):
        if name in self._reuse_map:
            return self._reuse_map[name]
        raise UnknownNameError()

    def _gather_reuse_map(self):
        self._reuse_map = {}
        tags = self._wikicode.filter_tags()
        for t in tags:
            if _tag_is_reusable_ref_tag(t):
                name = _get_ref_tag_name_value(t)
                self._reuse_map[name] = _get_ref_tag_cite_template(t)

    def _count_named_refs(self):
        tags = self._wikicode.filter_tags()
        return Counter([
                _get_ref_tag_name_value(t) for t in tags
                if (_tag_is_ref_tag(t) and _tag_has_name_attribute(t))
            ])

    def _count_all_citation_templates(self):
        templates = self._wikicode.filter_templates()
        return Counter([
            _standardize_template_string(t) for t in templates
            if _template_is_citation_template(t)
        ])
