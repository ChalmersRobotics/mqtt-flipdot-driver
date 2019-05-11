import serial
import io
import time, datetime

from display import DisplayBuffer, Font

def main():

    # 0x06 small display (42x16), 0x07 large display (112x16)
    smallSign = DisplayBuffer(0x06, 42, 16)
    largeSign = DisplayBuffer(0x07, 112, 16)

    with serial.serial_for_url("hwgrep://", baudrate=4800) as port:
        
        while True:
            # put some stuff 
            smallSign.put_text(datetime.datetime.now().strftime("%H:%M:%S"), 0, 4, Font.SMALL)

            #largeSign.put_text(datetime.datetime.now().strftime("%y:%m:%d %H:%M:%S"), 0, 8, SignFont.SMALL)

            # Write complete buffer to serial port
            buffer = largeSign.finalize_buffer()

            # try to combine the data into a sigle write just for fun ;)
            buffer.extend(smallSign.finalize_buffer())

            port.write(buffer)

            # print buffer for debugging
            print(','.join('0x{:02X}'.format(x) for x in buffer))

            time.sleep(1)

            
if __name__ == "__main__":
    main()