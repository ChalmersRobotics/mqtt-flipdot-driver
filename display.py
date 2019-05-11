import enum

class Font(enum.Enum):
    SMALL = (0x64, 5)
    BITMAP = (0x77, 5)

    def __init__(self, cmd, height):
        self.cmd = cmd
        self.height = height

class DisplayBuffer:
    """ Acts as a buffer for creating commands to send to the display """

    def __init__(self, address: int, width: int, height:int):
        self.address = address
        self.width = width
        self.height = height

        # create initial frame buffer
        self.reset_buffer()       
    
    def reset_buffer(self):
        self.buffer = bytearray()

        # add display header: 0xff (start), address, 0xA2 (always 0xA2)
        self.buffer.extend([0xff, self.address, 0xA2])

        # set display size
        self.buffer.extend([0xd0, self.width])  # width 
        self.buffer.extend([0xd1, self.height]) # height 

    def put_text(self, text:str,  x: int = 0, y: int = 0, font: Font = Font.SMALL):
        # set position (TODO: make the position aware of the font size, y-coordinate seems a bit fishy xD )
        self.buffer.extend([0xd2, x]) # x coordinate
        self.buffer.extend([0xd3, y]) # y coordinate

        # select font
        self.buffer.extend([0xd4, font.cmd])

        # write characters 
        self.buffer.extend([ord(c) for c in text])


    def put_bitmap(self, bitmap: bytearray, x: int = 0, y: int = 0):
        # set position
        self.buffer.extend([0xd2, x]) # x coordinate
        self.buffer.extend([0xd3, y]) # y coordinate

        # select bitmap font
        self.buffer.extend([0xd4, Font.BITMAP.cmd])

        # TODO: write real bitmap data here (somehow xD)
        self.buffer.extend(bitmap)
        
    def finalize_buffer(self) -> bytearray:
        """ completes the this frame and returns the bytes to be written to the display """
        
        # add checksum
        self._add_checksum(self.buffer)

        # add stop command
        self.buffer.append(0xff)

        # reset the buffer and return the old one
        buffer = self.buffer
        self.reset_buffer()

        return buffer

    @staticmethod
    def _add_checksum(data: bytearray):
        """ appends a checksum to the specified data """
        # sum all bytes except the first and take the lower 8 bits
        csum = sum(data[1:]) & 0xff

        # append checksum to data
        if csum == 0xfe:
            data.extend([0xfe, 0x00])
        elif csum == 0xff:
            data.extend([0xfe, 0x01])
        else:
            data.append(csum)
    
