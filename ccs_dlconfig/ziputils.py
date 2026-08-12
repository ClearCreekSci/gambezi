import os
import struct

MAX_COMMENT_LEN = 0xffff
EOCD_STRUCT_LEN = 22

SIG = b'\x50\x4b\x05\x06'

class ZipEocd:

    def __init__(self):
        signature = None           # Four-byte integer
        disk_number = None         # Two-byte integer
        disk_record_count = None   # Two-byte integer
        central_record_disk = None # Two-byte integer
        total_record_count = None  # Two-byte integer
        size = None                # Four-byte integer (size of central directory in bytes)
        offset = None              # Four-byte integer (offset to start of central directory)
        comment_length = None      # Two-byte integer
        comment = None             # Variable length byte array

    def read(self,path):
        global SIG
        st = os.stat(path)
        bytes_to_read = st.st_size
        if st.st_size >= (MAX_COMMENT_LEN + EOCD_STRUCT_LEN):
            bytes_to_read = MAX_COMMENT_LEN + EOCD_STRUCT_LEN
        idx = 0
        found = False
        with open(path,'rb') as fd:
            fd.seek(-bytes_to_read,os.SEEK_END)
            buf = fd.read(bytes_to_read)
            while idx < len(buf):
                if buf[idx] == SIG[0]:
                    if buf[idx+1] == SIG[1]:
                        if buf[idx+2] == SIG[2]:
                            if buf[idx+3] == SIG[3]:
                                found = True
                                break
                idx += 1
        if found:
            self.signature = struct.unpack('>i',buf[idx:idx+4])
            idx += 4
            self.disk_number = struct.unpack('>h',buf[idx:idx+2])
            idx += 2
            self.record_count = struct.unpack('>h',buf[idx:idx+2])
            idx += 2
            self.central_record_disk = struct.unpack('>h',buf[idx:idx+2])
            idx += 2
            self.total_record_count = struct.unpack('>h',buf[idx:idx+2])
            idx += 2
            self.size = struct.unpack('>h',buf[idx:idx+2])
            idx += 4
            self.offset = struct.unpack('>h',buf[idx:idx+2])
            idx += 4
            self.comment_length = struct.unpack('>h',buf[idx:idx+2])[0]
            idx += 2
            self.comment = buf[idx:idx+self.comment_length].decode('utf-8') 
        else:
            raise ValueError('EOCD magic value not found')




