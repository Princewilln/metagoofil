#!/usr/bin/env python3
import sys
try:
    from io import StringIO, BytesIO
except ImportError:
    from StringIO import StringIO
    from io import BytesIO


##  LZWDecoder
##
class LZWDecoder(object):

    debug = 0

    def __init__(self, fp):
        self.fp = fp
        self.buff = 0
        self.bpos = 8
        self.nbits = 9
        self.table = None
        self.prevbuf = None
        return

    def readbits(self, bits):
        v = 0
        while 1:
            # the number of remaining bits we can get from the current buffer.
            r = 8-self.bpos
            if bits <= r:
                # |-----8-bits-----|
                # |-bpos-|-bits-|  |
                # |      |----r----|
                v = (v<<bits) | ((self.buff>>(r-bits)) & ((1<<bits)-1))
                self.bpos += bits
                break
            else:
                # |-----8-bits-----|
                # |-bpos-|---bits----...
                # |      |----r----|
                v = (v<<r) | (self.buff & ((1<<r)-1))
                bits -= r
                x = self.fp.read(1)
                if not x: raise EOFError
                # Handle both bytes and str (Python 2/3 compatibility)
                if isinstance(x, bytes):
                    self.buff = x[0]  # In Python 3, bytes indexing returns int
                else:
                    self.buff = ord(x)  # In Python 2, str needs ord()
                self.bpos = 0
        return v

    def feed(self, code):
        x = b''
        if code == 256:
            self.table = [ bytes([c]) for c in range(256) ] # 0-255
            self.table.append(None) # 256
            self.table.append(None) # 257
            self.prevbuf = b''
            self.nbits = 9
        elif code == 257:
            pass
        elif not self.prevbuf:
            x = self.prevbuf = self.table[code]
        else:
            if code < len(self.table):
                x = self.table[code]
                self.table.append(self.prevbuf+x[:1])
            else:
                self.table.append(self.prevbuf+self.prevbuf[:1])
                x = self.table[code]
            l = len(self.table)
            if l == 511:
                self.nbits = 10
            elif l == 1023:
                self.nbits = 11
            elif l == 2047:
                self.nbits = 12
            self.prevbuf = x
        return x

    def run(self):
        while 1:
            try:
                code = self.readbits(self.nbits)
            except EOFError:
                break
            x = self.feed(code)
            yield x
            if self.debug:
                print(('nbits=%d, code=%d, output=%r, table=%r' %))
                                     (self.nbits, code, x, self.table[258:]))
        return

# lzwdecode
def lzwdecode(data):
    """
    >>> lzwdecode('\x80\x0b\x60\x50\x22\x0c\x0c\x85\x01')
    '\x2d\x2d\x2d\x2d\x2d\x41\x2d\x2d\x2d\x42'
    """
    fp = BytesIO(data) if isinstance(data, bytes) else StringIO(data)
    result = b''.join(x for x in LZWDecoder(fp).run() if x is not None)
    return result

if __name__ == '__main__':
    import doctest
    doctest.testmod()
