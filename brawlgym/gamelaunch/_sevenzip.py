"""
Extract ONE member from a 7z archive, in memory, including folders that use the BCJ2 filter.
"""
from __future__ import annotations

import io
import lzma
import re

_kTop = 1 << 24
_kNumBitModelTotalBits = 11
_kBitModelTotal = 1 << 11
_kNumMoveBits = 5


class _RangeDec:
    """
    LZMA-style binary range decoder over the BCJ2 'rc' control stream.
    """

    def __init__(self, data: bytes):
        self.data = data
        self.pos = 1                       # first rc byte is always ignored
        self.code = 0
        self.range = 0xFFFFFFFF
        for _ in range(4):
            self.code = ((self.code << 8) | self._byte()) & 0xFFFFFFFF

    def _byte(self) -> int:
        if self.pos < len(self.data):
            b = self.data[self.pos]
            self.pos += 1
            return b
        return 0

    def decode_bit(self, probs: list, idx: int) -> int:
        p = probs[idx]
        bound = (self.range >> _kNumBitModelTotalBits) * p
        if self.code < bound:
            self.range = bound
            probs[idx] = p + ((_kBitModelTotal - p) >> _kNumMoveBits)
            bit = 0
        else:
            self.range -= bound
            self.code -= bound
            probs[idx] = p - (p >> _kNumMoveBits)
            bit = 1
        if self.range < _kTop:
            self.range = (self.range << 8) & 0xFFFFFFFF
            self.code = ((self.code << 8) | self._byte()) & 0xFFFFFFFF
        return bit


_BRANCH = re.compile(rb"[\xe8\xe9]|\x0f[\x80-\x8f]")   # CALL, JMP, or two-byte Jcc


def _bcj2_decode(main: bytes, call: bytes, jump: bytes, rc: bytes, out_size: int) -> bytes:
    """
    Reconstruct the original stream from BCJ2's four inputs (main/call/jump/rc).
    """
    out = bytearray(out_size)
    probs = [_kBitModelTotal >> 1] * (256 + 2)
    rd = _RangeDec(rc)
    wp = mp = cp = jp = 0
    search = _BRANCH.search
    while wp < out_size:
        m = search(main, mp)
        if m is None:
            n = out_size - wp
            out[wp:wp + n] = main[mp:mp + n]
            wp += n
            break
        end = m.end()
        seg = end - mp
        out[wp:wp + seg] = main[mp:end]
        wp += seg
        mp = end
        b = out[wp - 1]
        prev = out[wp - 2] if wp >= 2 else 0
        idx = (2 + prev) if b == 0xE8 else (1 if b == 0xE9 else 0)
        if rd.decode_bit(probs, idx):
            src, sp = (call, cp) if b == 0xE8 else (jump, jp)
            val = (src[sp] << 24) | (src[sp + 1] << 16) | (src[sp + 2] << 8) | src[sp + 3]
            if b == 0xE8:
                cp += 4
            else:
                jp += 4
            dest = (val - (wp + 4)) & 0xFFFFFFFF
            out[wp] = dest & 0xff
            out[wp + 1] = (dest >> 8) & 0xff
            out[wp + 2] = (dest >> 16) & 0xff
            out[wp + 3] = (dest >> 24) & 0xff
            wp += 4
    return bytes(out)


def _dec_lzma1(data: bytes, props: bytes, out_size: int) -> bytes:
    d = props[0]
    lc = d % 9; d //= 9; lp = d % 5; pb = d // 5
    dict_size = int.from_bytes(props[1:5], "little")
    filt = [{"id": lzma.FILTER_LZMA1, "dict_size": max(dict_size, 4096), "lc": lc, "lp": lp, "pb": pb}]
    return lzma.LZMADecompressor(format=lzma.FORMAT_RAW, filters=filt).decompress(data, out_size)


def _dec_lzma2(data: bytes, props: bytes, out_size: int) -> bytes:
    b = props[0]
    dict_size = 0xFFFFFFFF if b >= 40 else (2 | (b & 1)) << (b // 2 + 11)
    filt = [{"id": lzma.FILTER_LZMA2, "dict_size": dict_size}]
    return lzma.LZMADecompressor(format=lzma.FORMAT_RAW, filters=filt).decompress(data, out_size)


def _decode_folder(folder, packed: list) -> bytes:
    """
    Decode a 7z folder's coder graph (generic: handles LZMA1/LZMA2 chains and the BCJ2 node).
    """
    coders = folder.coders
    in_index, out_index, inc, outc = [], [], 0, 0
    for c in coders:
        in_index.append(list(range(inc, inc + c["numinstreams"]))); inc += c["numinstreams"]
        out_index.append(list(range(outc, outc + c["numoutstreams"]))); outc += c["numoutstreams"]
    packed_for_in = {ing: packed[j] for j, ing in enumerate(folder.packed_indices)}
    bind_in_to_out = {b.incoder: b.outcoder for b in folder.bindpairs}
    unpack = folder.unpacksizes

    def coder_of_out(o):
        return next(ci for ci, outs in enumerate(out_index) if o in outs)

    memo = {}

    def get_output(ci):
        if ci in memo:
            return memo[ci]
        c = coders[ci]
        inputs = [packed_for_in[ing] if ing in packed_for_in
                  else get_output(coder_of_out(bind_in_to_out[ing]))
                  for ing in in_index[ci]]
        outsize = unpack[out_index[ci][0]]
        method = c["method"]
        if method == b"\x03\x01\x01":
            res = _dec_lzma1(inputs[0], c["properties"], outsize)
        elif method == b"\x21":
            res = _dec_lzma2(inputs[0], c["properties"], outsize)
        elif method == b"\x03\x03\x01\x1b":
            res = _bcj2_decode(inputs[0], inputs[1], inputs[2], inputs[3], outsize)
        else:
            raise NotImplementedError("unsupported 7z coder %s" % method.hex())
        memo[ci] = res
        return res

    used = {b.outcoder for b in folder.bindpairs}
    final_out = next(o for o in range(outc) if o not in used)
    return get_output(coder_of_out(final_out))


def extract_member(archive_bytes: bytes, matcher) -> bytes:
    """
    Return the bytes of the first content file whose name satisfies ``matcher(name)``.

    Uses py7zr to parse the header, then decodes only that file's folder in-memory. Raises
    NotImplementedError if the folder uses a coder we do not implement, KeyError/StopIteration
    if no member matches.
    """
    import py7zr
    z = py7zr.SevenZipFile(io.BytesIO(archive_bytes), "r")
    ms = z.header.main_streams
    folders = ms.unpackinfo.folders
    packsizes = ms.packinfo.packsizes
    off = 32 + ms.packinfo.packpos
    pack_offsets = []
    for s in packsizes:
        pack_offsets.append(off); off += s

    ss = ms.substreamsinfo
    content = [f for f in z.files if not f.emptystream]
    sizes = ss.unpacksizes
    fi_of_file, off_in_folder, k = [], [], 0
    for fi, cnt in enumerate(ss.num_unpackstreams_folders):
        acc = 0
        for _ in range(cnt):
            fi_of_file.append(fi); off_in_folder.append(acc); acc += sizes[k]; k += 1

    tgt = next(i for i, f in enumerate(content) if matcher(f.filename))
    fi = fi_of_file[tgt]
    pstart = sum(len(folders[j].packed_indices) for j in range(fi))
    packed = [archive_bytes[pack_offsets[pstart + j]:pack_offsets[pstart + j] + packsizes[pstart + j]]
              for j in range(len(folders[fi].packed_indices))]
    data = _decode_folder(folders[fi], packed)
    return data[off_in_folder[tgt]:off_in_folder[tgt] + sizes[tgt]]
