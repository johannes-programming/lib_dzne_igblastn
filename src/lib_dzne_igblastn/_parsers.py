
import os as _os
import string as _string

import simple_tsv as _tsv


class Parser:
    class Error(ValueError):
        pass
    def parse_text(text):
        lines = [Parser.parse_line(line) for line in text.split('\n')]
        blocks = [Parser.Block.from_chunk(chunk) for chunk in Parser.get_chunks_from_lines(lines)]
        return Parser.parse_blocks(blocks)
    def check(assertion, /, msg):
        if not assertion:
            raise Parser.Error(msg)
    def parse_value(value, /, datatype):
        if value == 'N/A':
            return float('nan')
        return datatype(value)
    def parse_bool(value):
        return {
            'no': False,
            'yes': True,
            'out-of-frame': False,
            'in-frame': True,
            'off': False,
            'on': True,
        }[value.lower()]
    def parse_line(line):
        if line == "":
            return None
        tab = '\t' in line
        sharp = line.startswith('#')
        Parser.check(tab + sharp < 2, "A line cannot start with '#' simultaneously contain tabs! ")
        if sharp:
            line = line.strip()
            #if line == "#":
            #    return ""
            #Parser.check(line.startswith("# ")
            return line[1:]
        if tab:
            ans, = (x for x in _tsv.reader([line.strip()]))
            return ans
        Parser.check(line.startswith("Total"), "Lines that do not start with '#' or contain tabs start with 'Total'!")
        k, v = [x.strip() for x in line.split('=')]# and contain exactly one '='! 
        return (k, int(v))
    def get_chunks_from_lines(lines):
        chunk = None
        for line in lines:
            if line is None:
                if chunk is not None:
                    yield chunk
                chunk = None
                continue
            if chunk is None:
                chunk = [line]
                continue
            chunk.append(line)
        if chunk is not None:
            yield chunk
    def parse_key(phrase):
        if phrase is None:
            return None
        phrase = phrase.strip()
        phrase = phrase.lower()
        phrase = phrase.replace('%', 'percent')
        ans = ""
        for ch in phrase:
            if ch in (_string.ascii_lowercase + _string.digits):
                ans += ch
            else:
                ans += '-'
        return ans.strip('-')
    def get_header_from_description(description, *, width):
        Parser.check(2 <= width, "A table must have at least two columns! ")
        for ch in [':', '(', ')']:
            description = description.replace(ch, '\n')
        headers = list()
        for splinter in description.split('\n'):
            part = splinter.strip(" ,")
            for phrase in ['i.e', ', or', ', and']:
                if phrase in part:
                    break
            else:
                header = part.split(',')
                if (width == len(header) + 1):
                    header = [None] + header
                if (width == len(header)):
                    headers.append(header)
        header, = headers
        header = [Parser.parse_key(col) for col in header]
        Parser.check(len(set(header)) == width, "The name of each column must be unique! ")
        return header
    def parse_blocks(blocks):
        ans = {
            'texts': list(),
            'tables': dict(),
        }
        for block in blocks:
            if type(block) is Parser.TextBlock:
                ans['texts'].append(block.data)
            elif type(block) is Parser.TotalBlock:
                Parser.check('totals' not in ans.keys(), "There can only be one totalblock! ")
                ans['totals'] = block.data
            elif type(block) is Parser.TabBlock:
                Parser.check(block.name not in ans['tables'].keys(), f"There can be only one table named {ascii(block.name)}")
                ans['tables'][block.name] = block.data
            else:
                raise TypeError(f"Type {type(block)} not allowed! ")
        return ans
    class Block:
        @property
        def data(self):
            return self._data
        def from_chunk(chunk):
            return {
                frozenset({str, list}): Parser.TabBlock,
                frozenset({tuple}): Parser.TotalBlock,
                frozenset({str}): Parser.TextBlock,
            }[frozenset(type(line) for line in chunk)](chunk)
            raise ValueError()
    class TextBlock(Block):
        def __init__(self, chunk):
            self._data = '\n'.join(chunk)
    class TotalBlock(Block):
        def __init__(self, chunk):
            self._data = dict()
            for k, v in chunk:
                key = Parser.parse_key(k)
                Parser.check(key not in self._data.keys(), "Every key must be unique! ")
                self._data[key] = v
    class TabBlock(Block):
        def _get_datatypess():
            return {
                'rearrangement': {
                    'top-v-gene-match': str,
                    'top-d-gene-match': str,
                    'top-j-gene-match': str,
                    'chain-type': str,
                    'stop-codon': Parser.parse_bool,
                    'v-j-frame': Parser.parse_bool,
                    'productive': Parser.parse_bool,
                    'strand': str,
                    'v-frame-shift': Parser.parse_bool,
                },
                'junction': {
                    'v-end': str,
                    'v-d-junction': str,
                    'd-region': str,
                    'd-j-junction': str,
                    'j-start': str,
                    'v-j-junction': str,
                },
                'sub-region': {
                    None: str,
                    'nucleotide-sequence': str,
                    'translation': str,
                    'start': int,
                    'end': int,
                },
                'alignment': {
                    None: str,
                    'from': int,
                    'to': int,
                    'length': int,
                    'matches': int,
                    'mismatches': int,
                    'gaps': int,
                    'percent-identity': float,
                },
                'hit': {
                    None: str,
                    'query-id': str,
                    'subject-id': str,
                    "percent-identity": float,
                    "alignment-length": int,
                    "mismatches": int,
                    "gap-opens": int,
                    "gaps": int,
                    "q--start": int,
                    "q--end": int,
                    "s--start": int,
                    "s--end": int,
                    "evalue": float,
                    "bit-score": float,
                    'query-seq': str,
                    'subject-seq': str,
                    'btop': str,
                },
            }
        def __init__(self, chunk):
            description = list()
            rows = list()
            width = None
            for line in chunk:
                if type(line) is str:
                    Parser.check(width is None, "The description comes before the datarows! ")
                    description.append(line)
                else:
                    Parser.check(type(line) is list, "A tabblock can only contain a description and datarows! ")
                    rows.append(line)
                    if width is None:
                        width = len(line)
                    else:
                        Parser.check(width == len(line), "The datarows in a table must have the same width! ")
            Parser.check(len(description), "Each tabblock must have a description! ") 
            Parser.check(len(rows), "Each tabblock must have at least one datarow! ")
            description = '\n'.join(description)
            _description = description.lower()
            signs = [
                'rearrangement summary',
                'junction details',
                'sub-region sequence details',
                'alignment summary',
                'hit table',
            ]
            sign, = [s for s in signs if (s in _description)]
            self._name = sign.split(' ')[0]
            header = Parser.get_header_from_description(description, width=width)
            dictReader = _tsv.DictReader(iter(rows), fieldnames=header)
            if None in header:
                body = dict()
            else:
                body = list()
            dtss = Parser.TabBlock._get_datatypess()
            for dictrow in dictReader:
                tablerow = dict()
                for col, elem in dictrow.items():
                    dt = dtss[self._name][col]
                    tablerow[col] = Parser.parse_value(elem, dt)
                if None in header:
                    index = Parser.parse_key(tablerow.pop(None))
                    if index not in body.keys():
                        body[index] = list()
                    body[index].append(tablerow)
                else:
                    body.append(tablerow)
            self._data = {
                'head': description,
                'body': body,
            }
        @property
        def name(self):
            return self._name
 
