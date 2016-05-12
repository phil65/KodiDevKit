import struct
import imghdr
import re
import functools
import os


@functools.lru_cache(maxsize=128)
def get_image_info(fname):
    '''Determine the image type of fhandle and return its size.
    from draco'''
    with open(fname, 'rb') as fhandle:
        head = fhandle.read(32)
        if len(head) != 32:
            return
        if imghdr.what(fname) == 'png':
            check = struct.unpack('>i', head[4:8])[0]
            if check != 0x0d0a1a0a:
                return
            info = [("Type", "png"),
                    ("Dimensions", "%sx%s" % (struct.unpack('>ii', head[16:24])))]
        elif imghdr.what(fname) == 'gif':
            info = [("Type", "gif"),
                    ("Dimensions", "%sx%s" % (struct.unpack('<HH', head[6:10])))]
        elif imghdr.what(fname) == 'jpeg':
            try:
                fhandle.seek(0)  # Read 0xff next
                size = 2
                ftype = 0
                while not 0xc0 <= ftype <= 0xcf:
                    fhandle.seek(size, 1)
                    byte = fhandle.read(1)
                    while ord(byte) == 0xff:
                        byte = fhandle.read(1)
                    ftype = ord(byte)
                    size = struct.unpack('>H', fhandle.read(2))[0] - 2
                # We are at a SOFn block
                fhandle.seek(1, 1)  # Skip `precision' byte.
                height, width = struct.unpack('>HH', fhandle.read(4))
                info = [("Type", "jpeg"),
                        ("Dimensions", "%sx%s" % (width, height)),
                        ("is_progressive", is_progressive(fname))]
            except Exception:  # IGNORE:W0703
                return
        elif imghdr.what(fname) == 'pgm':
            header, width, height, maxval = re.search(
                b"(^P5\s(?:\s*#.*[\r\n])*"
                b"(\d+)\s(?:\s*#.*[\r\n])*"
                b"(\d+)\s(?:\s*#.*[\r\n])*"
                b"(\d+)\s(?:\s*#.*[\r\n]\s)*)", head).groups()
            info = [("Type", "pgm"),
                    ("Dimensions", "%sx%s" % (width, height)),
                    ("maxval", maxval),
                    ("Header", header)]
        elif imghdr.what(fname) == 'bmp':
            _, width, height, depth = re.search(
                b"((\d+)\sx\s"
                b"(\d+)\sx\s"
                b"(\d+))", str).groups()
            info = [("Type", "bmp"),
                    ("Dimensions", "%sx%s" % (width, height)),
                    ("Depth", depth)]
        else:
            return
        info.append(("File size", "%.2f kb" % (os.path.getsize(fname) / 1024)))
        return info


@functools.lru_cache(maxsize=128)
def is_progressive(filename):
    with open(filename, "rb") as f:
        while True:
            blockStart = struct.unpack('B', f.read(1))[0]
            if blockStart != 0xff:
                raise ValueError('Invalid char code ' + blockStart + ' - not a JPEG file: ' + filename)
                return False

            blockType = struct.unpack('B', f.read(1))[0]
            if blockType == 0xd8:   # Start Of Image
                continue
            elif blockType == 0xc0:  # Start of baseline frame
                return False
            elif blockType == 0xc2:  # Start of progressive frame
                return True
            elif blockType >= 0xd0 and blockType <= 0xd7:  # Restart
                continue
            elif blockType == 0xd9:  # End Of Image
                break
            else:                   # Variable-size block, just skip it
                blockSize = struct.unpack('2B', f.read(2))
                blockSize = blockSize[0] * 256 + blockSize[1] - 2
                f.seek(blockSize, 1)
    return False
