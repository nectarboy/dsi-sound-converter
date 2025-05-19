# converts DSi Sound formatted sound files to signed PCM16 sound files
# nectarboy 2025
import sys
import os
from pathlib import Path
import shutil

SAMPLE_RATE = 16384
SOUND_FILE_SIZE = 82946
MAX_SAMPLE_COUNT = 81840 * 2

# filepath = "voice/voice00140902154310000320001.dat" # tunnel
# filepath = "voice/voice05101204154419003410001.dat" 
# filepath = "voice/voice06101215154440003410001.dat" 
# filepath = "voice/voice08101122144249001210001.dat"
# filepath = "voice/voice10101122100657000110001.dat" # classical music
# filepath = "voice/voice13101122144527000310001.dat"
# filepath = "voice/voice15101122101148003110001.dat" # background conversation
# filepath = "voice/voice17101122100515003210001.dat" # recording
# filepath = "voice/voice19121009123451000010001.dat" # unknown ??? doesnt show up in DSi sound
#filepath = "voice/test.dat"

# test
#filepath = "voicetests/voice10101123164207001410001.dat"

def readS8(arr, addr):
    val = arr[addr]
    if val & 0x80:
        val -= 0x100
    return val
def readU16LE(arr, addr):
    return arr[addr] | (arr[addr+1] << 8)
def readS16LE(arr, addr):
    val = readU16LE(arr,addr)
    if val & 0x8000:
        val -= 0x10000
    return val
def readU32LE(arr, addr):
    return arr[addr] | (arr[addr+1] << 8) | (arr[addr+2] << 12) | (arr[addr+3] << 16)
def readS32LE(arr, addr):
    val = readU32LE(arr,addr)
    if val & 0x80000000:
        val -= 0x100000000
    return val

# step size
ss_lut_dsi_bytes = [ 0x07, 0x00, 0x08, 0x00, 0x09, 0x00, 0x0a, 0x00, 0x0b, 0x00, 0x0c, 0x00, 0x0d, 0x00, 0x0e, 0x00, 0x10, 0x00, 0x11, 0x00, 0x13, 0x00, 0x15, 0x00, 0x17, 0x00, 0x19, 0x00, 0x1c, 0x00, 0x1f, 0x00, 0x22, 0x00, 0x25, 0x00, 0x29, 0x00, 0x2d, 0x00, 0x32, 0x00, 0x37, 0x00, 0x3c, 0x00, 0x42, 0x00, 0x49, 0x00, 0x50, 0x00, 0x58, 0x00, 0x61, 0x00, 0x6b, 0x00, 0x76, 0x00, 0x82, 0x00, 0x8f, 0x00, 0x9d, 0x00, 0xad, 0x00, 0xbe, 0x00, 0xd1, 0x00, 0xe6, 0x00, 0xfd, 0x00, 0x17, 0x01, 0x33, 0x01, 0x51, 0x01, 0x73, 0x01, 0x98, 0x01, 0xc1, 0x01, 0xee, 0x01, 0x20, 0x02, 0x56, 0x02, 0x92, 0x02, 0xd4, 0x02, 0x1c, 0x03, 0x6c, 0x03, 0xc3, 0x03, 0x24, 0x04, 0x8e, 0x04, 0x02, 0x05, 0x83, 0x05, 0x10, 0x06, 0xab, 0x06, 0x56, 0x07, 0x12, 0x08, 0xe0, 0x08, 0xc3, 0x09, 0xbd, 0x0a, 0xd0, 0x0b, 0xff, 0x0c, 0x4c, 0x0e, 0xba, 0x0f, 0x4c, 0x11, 0x07, 0x13, 0xee, 0x14, 0x06, 0x17, 0x54, 0x19, 0xdc, 0x1b, 0xa5, 0x1e, 0xb6, 0x21, 0x15, 0x25, 0xca, 0x28, 0xdf, 0x2c, 0x5b, 0x31, 0x4b, 0x36, 0xb9, 0x3b, 0xb2, 0x41, 0x44, 0x48, 0x7e, 0x4f, 0x71, 0x57, 0x2f, 0x60, 0xce, 0x69, 0x62, 0x74, 0xff, 0x7f ]
ss_lut = []
for i in range(len(ss_lut_dsi_bytes)//2):
    ss_lut.append(ss_lut_dsi_bytes[i*2] | (ss_lut_dsi_bytes[i*2 + 1] << 8))

def convert():
    if len(sys.argv) < 2:
        print("Not enough arguments provided, format: convert.py path -p")
        print("path: path to a voice file or folder to convert all voice files")
        print("-p: (optional) playback converted file")
        return

    filepathstr = sys.argv[1]
    path = Path(filepathstr)
    filenames = []
    convertingDirectory = False
    validConversions = 0

    if not path.exists():
        print("Path doesn't exist.")
        return
    elif path.is_dir():
        print("Path is a directory.")
        filenames = os.listdir(filepathstr)
        filenames = [f for f in filenames if os.path.isfile(filepathstr + '/' + f)]
        convertingDirectory = True
    else:
        filenames = [filepathstr]


    for name in filenames:
        dirstr = name
        if convertingDirectory:
            dirstr = filepathstr + "/" + name

        # create new converted file path
        convertedfilepath = dirstr.split(".")
        # skip non .dat files
        if len(convertedfilepath) == 1 or convertedfilepath[len(convertedfilepath)-1] != "dat":
            if not convertingDirectory:
                print(dirstr, "is not a .dat file.")
            continue
        # file is .dat file
        else:
            convertedfilepath.pop()
            convertedfilepath = "".join(convertedfilepath) + ".wav"

        print('converting', dirstr + '...')

        # decoding adpcm to pcm16
        bin = list(open(dirstr, 'rb').read())

        # check if its a valid sound file
        if (
            len(bin) != SOUND_FILE_SIZE or
            bin[0] != 0x02 or
            bin[1] != 0x00 or
            bin[2] != 0xec or
            bin[3] != 0x3f
            ):
            print(dirstr, "is not a valid sound file.")
            continue

        samplesCount = readU16LE(bin, 8) * 8 # TODO, properly calc this by counting empty space in file
        out = readS16LE(bin, 0xc)
        ssi = readS8(bin, 0xc+1)
        ss = ss_lut[0]

        pcmdata = []

        i = 0
        while True:
            sample = (bin[i//2 + 0x10] >> (((i) & 1)*4)) & 0xf
            sign = sample >> 3
            mag = sample & 7

            # step size index calculation
            if mag < 4:
                ssi -= 1
            else:
                ssi += 2*(mag - 3)

            if ssi < 0:
                ssi = 0
            elif ssi >= 0x58:
                ssi = 0x58


            # difference calculation
            d = ss >> 3;
            if (sample & 4) != 0:
                d += ss
            if (sample & 2) != 0:
                d += (ss >> 1)
            if (sample & 1) != 0:
                d += (ss >> 2);

            if sign:
                d = -d

            # out += d
            # if out > 32767:
            #     out = 32767
            # elif out < -32768:
            #     out = -32768
            d += out
            out = 0x7fff
            if d < 0x8000:
                out = d
                if d < -0x8000:
                    out = -0x8000

            ss = ss_lut[ssi]


            # mixing (little endian pcm 16 signed)
            finalout = 0xffff & out
            pcmdata.append(finalout & 0xff)
            pcmdata.append(finalout >> 8)

            # lin int?
            # if i > 0:
            #     lastout = (pcmdata[i*4 - 4]) | (pcmdata[i*4 - 4 + 1] << 8)
            #     if (lastout >> 15) & 1:
            #         lastout = lastout - 0x10000

            #     avg = 0xffff & ((out + lastout) // 2)
            #     pcmdata[i*4 - 2] = avg & 0xff
            #     pcmdata[i*4 - 2 + 1] = avg >> 8

            i += 1
            if (i >= samplesCount and ssi == 0) or i >= MAX_SAMPLE_COUNT:
                break

        # creating wav header
        # riff
        wavheader = [0] * 44
        wavheader[0] = ord('R')
        wavheader[1] = ord('I')
        wavheader[2] = ord('F')
        wavheader[3] = ord('F')
        # filesize
        filesize = len(wavheader) + len(pcmdata)
        wavheader[4] = (filesize >> 0) & 0xff
        wavheader[5] = (filesize >> 8) & 0xff
        wavheader[6] = (filesize >> 16) & 0xff
        wavheader[7] = (filesize >> 24) & 0xff
        # wave
        wavheader[8] = ord('W')
        wavheader[9] = ord('A')
        wavheader[10] = ord('V')
        wavheader[11] = ord('E')
        # fmt
        wavheader[12] = 0x66;
        wavheader[13] = 0x6d;
        wavheader[14] = 0x74;
        wavheader[15] = 0x20;
        wavheader[16] = 16;
        wavheader[17] = 0;
        wavheader[18] = 0;
        wavheader[19] = 0;
        # pcm
        wavheader[20] = 1
        # 1 ch
        wavheader[22] = 1
        # sample rate
        wavheader[24] = (SAMPLE_RATE >> 0) & 0xff
        wavheader[25] = (SAMPLE_RATE >> 8) & 0xff
        wavheader[26] = (SAMPLE_RATE >> 16) & 0xff
        wavheader[27] = (SAMPLE_RATE >> 24) & 0xff
        # byte rate
        byterate = SAMPLE_RATE * 16 // 8
        wavheader[28] = (byterate >> 0) & 0xff
        wavheader[29] = (byterate >> 8) & 0xff
        wavheader[30] = (byterate >> 16) & 0xff
        wavheader[31] = (byterate >> 24) & 0xff
        # block align (2)
        wavheader[32] = 2
        # bit depth (16)
        wavheader[34] = 16
        # data
        wavheader[36] = ord('d')
        wavheader[37] = ord('a')
        wavheader[38] = ord('t')
        wavheader[39] = ord('a')
        wavheader[40] = (len(pcmdata) >> 0) & 0xff
        wavheader[41] = (len(pcmdata) >> 8) & 0xff
        wavheader[42] = (len(pcmdata) >> 16) & 0xff
        wavheader[43] = (len(pcmdata) >> 24) & 0xff

        # writeback
        wavfile = wavheader + pcmdata
        with open(convertedfilepath, "wb") as f:
            f.write(bytes(wavfile))

        validConversions += 1

    if validConversions != 0:
        print("done!")

        # playback
        if not convertingDirectory and len(sys.argv) >= 3 and sys.argv[2] == '-p':
            import pyaudio

            print('playing', convertedfilepath)
            player = pyaudio.PyAudio()
            stream = player.open(
                format = pyaudio.paInt16,
                channels = 1,
                rate = 16384,
                output = True
            )
            stream.write(bytes(pcmdata))
            stream.close()
            player.terminate()
    elif convertingDirectory:
        print("No valid .dat files found.")

convert()