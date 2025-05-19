# dsi-sound-converter
A script to convert voice memos from the DSi Sound app to wav files

# DSi Voice Memo Files
The DSi Sound app stores voice memos in IMA ADPCM format at a sample rate of 16384, packaged in .dat files containing a header, data block, and footer.
The header is 16 bytes, and contains the number of samples.
The footer contains a string of the voice memo's timestamp, and a CRC16 checksum is appended to the end of the file.

# Usage
To convert from voice memos to 16 bit WAV files, run
```sh
convert.py path -p
```
`path` can be a single file or a directory of files to convert

`-p` can be optionally included to playback the file if converting a single file. (You will need to have the PyAudio package installed)
