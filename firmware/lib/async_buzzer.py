"""Module to play tunes on SparkFun's Qwiic buzzer 

Some functions use a default volume that can be changed using the global variable DEFAULT_VOLUME
"""

import asyncio

DEFAULT_VOLUME = 3

class AsyncI2CBuzzer:
    """Reads a playlist of notes and plays them timely on Sparkfun's Qwiic Buzzer using asyncio
    
    A playlist is a list of notes, and each note is defined as a tuple containing:
    1. frequency: an integer with Hz as units
    2. volume: an integer from 0 (quiet) to 4 (loud)
    3. duration: an integer with milliseconds as unit
    """
    
    def __init__(self, i2c, addr = 52):
        """Initializes AsyncBuzzer
        
        Arguments are:
        - i2c: The I2C class from the machine module.
        - addr: address of the buzzer
        """
        self.i2c = i2c
        self.addr = addr
        self.notes_to_play = []
        self.player_task = None
        
    def __send_note(self, freq, volume, duration):
        msg = freq.to_bytes(2, 'big') + volume.to_bytes(1, 'big') + duration.to_bytes(2, 'big') + b'\x01'
        self.i2c.writeto_mem(self.addr, 3, msg)
        
    async def __play_notes(self):
        while self.notes_to_play:
            next_note = self.notes_to_play.pop(0)
            # send note but only for 99% of the duration, to avoid
            # a race condition between the buzzer's I2C and note playing
            self.__send_note(next_note[0], next_note[1], int(0.99*next_note[2]))
            await asyncio.sleep_ms(next_note[2])

        self.player_task = None
            
    def add(self, notes: list):
        """Appends a list of notes at the end of the playlist.
        
        See class description for the definition on notes"""
        self.notes_to_play.extend(notes)
        if not self.player_task:
            self.player_task = asyncio.create_task(self.__play_notes())
        
    def replace(self, notes: list):
        """Stops what is currently playing and replaces it with the provided note list. 
        
        See class description for the definition on notes"""
        self.notes_to_play = notes
        if self.player_task:
            self.player_task.cancel()
        self.player_task = asyncio.create_task(self.__play_notes())
        
    def is_playing(self):
        """Returns True if the playlist is still actively playing."""
        
        return self.player_task is not None

class Pitches:
    """A class that contains static currespondance between pitch letters and frequencies in Hz"""
    S = 0
    B0 = 31
    C1 = 33
    CS1 = 35
    D1 = 37
    DS1 = 39
    E1 = 41
    F1 = 44
    FS1 = 46
    G1 = 49
    GS1 = 52
    A1 = 55
    AS1 = 58
    B1 = 62
    C2 = 65
    CS2 = 69
    D2 = 73
    DS2 = 78
    E2 = 82
    F2 = 87
    FS2 = 93
    G2 = 98
    GS2 = 104
    A2 = 110
    AS2 = 117
    B2 = 123
    C3 = 131
    CS3 = 139
    D3 = 147
    DS3 = 156
    E3 = 165
    F3 = 175
    FS3 = 185
    G3 = 196
    GS3 = 208
    A3 = 220
    AS3 = 233
    B3 = 247
    C4 = 262
    CS4 = 277
    D4 = 294
    DS4 = 311
    E4 = 330
    F4 = 349
    FS4 = 370
    G4 = 392
    GS4 = 415
    A4 = 440
    AS4 = 466
    B4 = 494
    C5 = 523
    CS5 = 554
    D5 = 587
    DS5 = 622
    E5 = 659
    F5 = 698
    FS5 = 740
    G5 = 784
    GS5 = 831
    A5 = 880
    AS5 = 932
    B5 = 988
    C6 = 1047
    CS6 = 1109
    D6 = 1175
    DS6 = 1245
    E6 = 1319
    F6 = 1397
    FS6 = 1480
    G6 = 1568
    GS6 = 1661
    A6 = 1760
    AS6 = 1865
    B6 = 1976
    C7 = 2093
    CS7 = 2217
    D7 = 2349
    DS7 = 2489
    E7 = 2637
    F7 = 2794
    FS7 = 2960
    G7 = 3136
    GS7 = 3322
    A7 = 3520
    AS7 = 3729
    B7 = 3951
    C8 = 4186
    CS8 = 4435
    D8 = 4699
    DS8 = 4978
        
def text_to_morse_notes(text, short_note, long_note = None, sep_units = (1, 3, 7)):
    """Translates text to music notes using Morse code.
    
    Returns a list of tuples that can be used by AsyncBuzzer
    text is a string that will be converted to morse code. Should contain alphanumeric and space characters
    short_note defines the dot sound and needs to be a tuple compatible with AsyncBuzzer
    long_note defines the dash sound and needs to be a tuple compatible with AsyncBuzzer
    if long_note is not provided, it will be like short_note, but 3 times longer 
    sep_units is a tuple of 3 numbers, defining the silence between 2 notes, a letter, and a word respectively
    sep_units is by default the standard (1, 3, 7)
    """
    if not long_note:
        long_note = (short_note[0], short_note[1], 3*short_note[2])
        
    silent_note = (Pitches.S, 0, int(sep_units[0]*short_note[2]))
    letter_sep = (Pitches.S, 0, int(sep_units[1]*short_note[2]))
    word_sep = (Pitches.S, 0, int(sep_units[2]*short_note[2]))
        
    morse_notes = []
    for symbol in text:
        symbol = symbol.lower()
        if symbol == ' ':
            morse_notes.extend([word_sep])
        elif symbol == 'a':
            morse_notes.extend([short_note, silent_note, long_note, letter_sep])
        elif symbol == 'b':
            morse_notes.extend([long_note, silent_note, short_note, silent_note, short_note, silent_note, short_note, letter_sep])
        elif symbol == 'c':
            morse_notes.extend([long_note, silent_note, short_note, silent_note, long_note, silent_note, short_note, letter_sep])
        elif symbol == 'd':
            morse_notes.extend([long_note, silent_note, short_note, silent_note, short_note, letter_sep])
        elif symbol == 'e':
            morse_notes.extend([short_note, letter_sep])
        elif symbol == 'f':
            morse_notes.extend([short_note, silent_note, short_note, silent_note, long_note, silent_note, short_note, letter_sep])
        elif symbol == 'g':
            morse_notes.extend([long_note, silent_note, long_note, silent_note, short_note, letter_sep])
        elif symbol == 'h':
            morse_notes.extend([short_note, silent_note, short_note, silent_note, short_note, silent_note, short_note, letter_sep])
        elif symbol == 'i':
            morse_notes.extend([short_note, silent_note, short_note, letter_sep])
        elif symbol == 'j':
            morse_notes.extend([short_note, silent_note, long_note, silent_note, long_note, silent_note, long_note, letter_sep])
        elif symbol == 'k':
            morse_notes.extend([long_note, silent_note, short_note, silent_note, long_note, letter_sep])
        elif symbol == 'l':
            morse_notes.extend([short_note, silent_note, long_note, silent_note, short_note, silent_note, short_note, letter_sep])
        elif symbol == 'm':
            morse_notes.extend([long_note, silent_note, long_note, letter_sep])
        elif symbol == 'n':
            morse_notes.extend([long_note, silent_note, short_note, letter_sep])
        elif symbol == 'o':
            morse_notes.extend([long_note, silent_note, long_note, silent_note, long_note, letter_sep])
        elif symbol == 'p':
            morse_notes.extend([short_note, silent_note, long_note, silent_note, long_note, silent_note, short_note, letter_sep])
        elif symbol == 'q':
            morse_notes.extend([long_note, silent_note, long_note, silent_note, short_note, silent_note, long_note, letter_sep])
        elif symbol == 'r':
            morse_notes.extend([short_note, silent_note, long_note, silent_note, short_note, letter_sep])
        elif symbol == 's':
            morse_notes.extend([short_note, silent_note, short_note, silent_note, short_note, letter_sep])
        elif symbol == 't':
            morse_notes.extend([long_note, letter_sep])
        elif symbol == 'u':
            morse_notes.extend([short_note, silent_note, short_note, silent_note, long_note, letter_sep])
        elif symbol == 'v':
            morse_notes.extend([short_note, silent_note, short_note, silent_note, short_note, silent_note, long_note, letter_sep])
        elif symbol == 'w':
            morse_notes.extend([short_note, silent_note, long_note, silent_note, long_note, letter_sep])
        elif symbol == 'x':
            morse_notes.extend([long_note, silent_note, short_note, silent_note, short_note, silent_note, long_note, letter_sep])
        elif symbol == 'y':
            morse_notes.extend([long_note, silent_note, short_note, silent_note, long_note, silent_note, long_note, letter_sep])
        elif symbol == 'z':
            morse_notes.extend([long_note, silent_note, long_note, silent_note, short_note, silent_note, short_note, letter_sep])
        elif symbol == '1':
            morse_notes.extend([short_note, silent_note, long_note, silent_note, long_note, silent_note, long_note, silent_note, long_note, letter_sep])
        elif symbol == '2':
            morse_notes.extend([short_note, silent_note, short_note, silent_note, long_note, silent_note, long_note, silent_note, long_note, letter_sep])
        elif symbol == '3':
            morse_notes.extend([short_note, silent_note, short_note, silent_note, short_note, silent_note, long_note, silent_note, long_note, letter_sep])
        elif symbol == '4':
            morse_notes.extend([short_note, silent_note, short_note, silent_note, short_note, silent_note, short_note, silent_note, long_note, letter_sep])
        elif symbol == '5':
            morse_notes.extend([short_note, silent_note, short_note, silent_note, short_note, silent_note, short_note, silent_note, short_note, letter_sep])
        elif symbol == '6':
            morse_notes.extend([long_note, silent_note, short_note, silent_note, short_note, silent_note, short_note, silent_note, short_note, letter_sep])
        elif symbol == '7':
            morse_notes.extend([long_note, silent_note, long_note, silent_note, short_note, silent_note, short_note, silent_note, short_note, letter_sep])
        elif symbol == '8':
            morse_notes.extend([long_note, silent_note, long_note, silent_note, long_note, silent_note, short_note, silent_note, short_note, letter_sep])
        elif symbol == '9':
            morse_notes.extend([long_note, silent_note, long_note, silent_note, long_note, silent_note, long_note, silent_note, short_note, letter_sep])
        elif symbol == '0':
            morse_notes.extend([long_note, silent_note, long_note, silent_note, long_note, silent_note, long_note, silent_note, long_note, letter_sep])
            
    return morse_notes
    
def tabs_to_notes(tabs, volume = None, unit_length = 400):
    """Converts text containing tabs to note list.
    
    tabs:
    - a string of notes
    - Each note is separated by a space " "
    - First characters define pitch, following the Pitches class nomencrature
    - An optional last character defines note length as follows:
        - "!" 1/8 unit_length
        - ":" 1/4 unit_length
        - ";" 1/3 unit_length
        - "." 1/2 unit_length
        - nothing: 1 unit_length
        - "*" 1.5 unit_length
        - "-" 2 unit_length
        - "~" 3 unit_length
        - "_" 4 unit_length
    volume: integer between 0 and 4 included. If not provided, DEFAULT_VOLUME is used
    unit_length: integer, length of a regular note, in milliseconds
    """
    
    if volume == None:
        volume = DEFAULT_VOLUME
    
    notes = []
    
    for txt_note in tabs.split(' '):
        if txt_note[-1] in '!:;.*-~_':
            if txt_note[-1] == '!':
                length = unit_length/8
            if txt_note[-1] == ':':
                length = unit_length/4
            if txt_note[-1] == ';':
                length = unit_length/3
            if txt_note[-1] == '.':
                length = unit_length/2
            if txt_note[-1] == '*':
                length = 3*unit_length/2
            if txt_note[-1] == '-':
                length = 2*unit_length
            if txt_note[-1] == '~':
                length = 3*unit_length
            if txt_note[-1] == '_':
                length = 4*unit_length
            txt_note = txt_note[:-1]
        else:
            length = unit_length
            
        pitch = getattr(Pitches, txt_note)
        
        notes.append((pitch, volume, int(length)))
        
    return notes 
    
    
def text_to_tunetalk_tabs(text, octave = 4):
    """Translates a text to a tune in the form of tabs.
    
    Only letters and space are considered. Notes span an octave.
    Vowels are a single long note, consonants are two short notes.
    Each letter is separated by a short silence.
    the octave argument is an integer that allows to choose the pitch by octave increments
    """
    
    tabs = ''
    octave = str(octave)
    
    for symbol in text:
        symbol = symbol.lower()
        if symbol == ' ':
            tabs += 'S- S: '
        elif symbol == 'a':
            tabs += 'F'+octave+'- S: '
        elif symbol == 'b':
            tabs += 'E'+octave+' C'+octave+' S: ' 
        elif symbol == 'c':
            tabs += 'A'+octave+' D'+octave+' S: ' 
        elif symbol == 'd':
            tabs += 'F'+octave+' D'+octave+' S: ' 
        elif symbol == 'e':
            tabs += 'A'+octave+'- S: '
        elif symbol == 'f':
            tabs += 'E'+octave+' A'+octave+' S: ' 
        elif symbol == 'g':
            tabs += 'D'+octave+' C'+octave+' S: ' 
        elif symbol == 'h':
            tabs += 'G'+octave+' A'+octave+' S: ' 
        elif symbol == 'i':
            tabs += 'B'+octave+'- S: '
        elif symbol == 'j':
            tabs += 'A'+octave+' B'+octave+' S: ' 
        elif symbol == 'k':
            tabs += 'A'+octave+' F'+octave+' S: ' 
        elif symbol == 'l':
            tabs += 'D'+octave+' F'+octave+' S: ' 
        elif symbol == 'm':
            tabs += 'F'+octave+' A'+octave+' S: ' 
        elif symbol == 'n':
            tabs += 'E'+octave+' G'+octave+' S: ' 
        elif symbol == 'o':
            tabs += 'E'+octave+'- S: '
        elif symbol == 'p':
            tabs += 'G'+octave+' E'+octave+' S: ' 
        elif symbol == 'q':
            tabs += 'A'+octave+' E'+octave+' S: ' 
        elif symbol == 'r':
            tabs += 'D'+octave+' G'+octave+' S: ' 
        elif symbol == 's':
            tabs += 'F'+octave+' B'+octave+' S: ' 
        elif symbol == 't':
            tabs += 'B'+octave+' G'+octave+' S: ' 
        elif symbol == 'u':
            tabs += 'D'+octave+'- S: '
        elif symbol == 'v':
            tabs += 'C'+octave+' E'+octave+' S: ' 
        elif symbol == 'w':
            tabs += 'C'+octave+' F'+octave+' S: ' 
        elif symbol == 'x':
            tabs += 'A'+octave+' C'+octave+' S: ' 
        elif symbol == 'y':
            tabs += 'G'+octave+'- S: '
        elif symbol == 'z':
            tabs += 'G'+octave+' D'+octave+' S: ' 
        else:
            tabs += 'C2- S: ' 
            
    return tabs[:-1]
    
def yes(freq_scaling = 1.0, volume = None, duration_scaling = 1.0):
    """Make a "yes" tune
    
    freq_scaling: a float that scales the pitch of the notes
    volume: integer between 0 and 4 included. If not provided, DEFAULT_VOLUME is used
    duration_scaling: a float that scales the duration of the notes 
    """
    if volume == None:
        volume = DEFAULT_VOLUME
    return [(int(freq_scaling*Pitches.C5), volume, int(duration_scaling*150)),
            (int(freq_scaling*Pitches.E5), volume, int(duration_scaling*250))]

def no(freq_scaling = 1.0, volume = None, duration_scaling = 1.0):
    """Make a "no" tune
    
    freq_scaling: a float that scales the pitch of the notes
    volume: integer between 0 and 4 included. If not provided, DEFAULT_VOLUME is used
    duration_scaling: a float that scales the duration of the notes 
    """
    if volume == None:
        volume = DEFAULT_VOLUME
    return [(int(freq_scaling*Pitches.C5), volume, int(duration_scaling*200)),
            (int(freq_scaling*Pitches.A4), volume, int(duration_scaling*300))]

def wrong(freq_scaling = 1.0, volume = None, duration_scaling = 1.0):
    """Make a "wrong!" tune
    
    freq_scaling: a float that scales the pitch of the notes
    volume: integer between 0 and 4 included. If not provided, DEFAULT_VOLUME is used
    duration_scaling: a float that scales the duration of the notes 
    """
    if volume == None:
        volume = DEFAULT_VOLUME
    return [(int(freq_scaling*Pitches.C3), volume, int(duration_scaling*800))]

def victory(freq_scaling = 1.0, volume = None, duration_scaling = 1.0):
    """Make a "vixtory" tune
    
    freq_scaling: a float that scales the pitch of the notes
    volume: integer between 0 and 4 included. If not provided, DEFAULT_VOLUME is used
    duration_scaling: a float that scales the duration of the notes 
    """
    if volume == None:
        volume = DEFAULT_VOLUME
    return [(int(freq_scaling*Pitches.C5), volume, int(duration_scaling*150)),
            (int(freq_scaling*Pitches.E5), volume, int(duration_scaling*150)),
            (int(freq_scaling*Pitches.C5), volume, int(duration_scaling*150)),
            (int(freq_scaling*Pitches.F5), volume, int(duration_scaling*300))]

def laugh(freq_scaling = 1.0, volume = None, duration_scaling = 1.0):
    """Make a "laugh" tune
    
    freq_scaling: a float that scales the pitch of the notes
    volume: integer between 0 and 4 included. If not provided, DEFAULT_VOLUME is used
    duration_scaling: a float that scales the duration of the notes 
    """
    if volume == None:
        volume = DEFAULT_VOLUME
    return [(int(freq_scaling*Pitches.F5), volume, int(duration_scaling*100)),
            (int(freq_scaling*Pitches.E5), volume, int(duration_scaling*200)),
            (int(freq_scaling*Pitches.F5), volume, int(duration_scaling*100)),
            (int(freq_scaling*Pitches.E5), volume, int(duration_scaling*200)),
            (int(freq_scaling*Pitches.F5), volume, int(duration_scaling*100)),
            (int(freq_scaling*Pitches.E5), volume, int(duration_scaling*200)),
            (int(freq_scaling*Pitches.F5), volume, int(duration_scaling*100)),
            (int(freq_scaling*Pitches.E5), volume, int(duration_scaling*200))]
            

def sad(freq_scaling = 1.0, volume = None, duration_scaling = 1.0):
    """Make a "sad" tune
    
    freq_scaling: a float that scales the pitch of the notes
    volume: integer between 0 and 4 included. If not provided, DEFAULT_VOLUME is used
    duration_scaling: a float that scales the duration of the notes 
    """
    if volume == None:
        volume = DEFAULT_VOLUME
    return [(int(freq_scaling*Pitches.F4), volume, int(duration_scaling*400)),
            (int(freq_scaling*Pitches.E4), volume, int(duration_scaling*400)),
            (int(freq_scaling*Pitches.DS4), volume, int(duration_scaling*400)),
            (int(freq_scaling*Pitches.D4), volume, int(duration_scaling*400))]
            
def siren(freq_scaling = 1.0, volume = None, duration_scaling = 1.0):
    """Make a "siren" tune
    
    freq_scaling: a float that scales the pitch of the notes
    volume: integer between 0 and 4 included. If not provided, DEFAULT_VOLUME is used
    duration_scaling: a float that scales the duration of the notes 
    """
    if volume == None:
        volume = DEFAULT_VOLUME
    pass

    return [(int(freq_scaling*Pitches.FS5), volume, int(duration_scaling*400)),
            (int(freq_scaling*Pitches.C5), volume, int(duration_scaling*400)),
            (int(freq_scaling*Pitches.FS5), volume, int(duration_scaling*400)),
            (int(freq_scaling*Pitches.C5), volume, int(duration_scaling*400)),
            (int(freq_scaling*Pitches.FS5), volume, int(duration_scaling*400)),
            (int(freq_scaling*Pitches.C5), volume, int(duration_scaling*400)),
            (int(freq_scaling*Pitches.FS5), volume, int(duration_scaling*400)),
            (int(freq_scaling*Pitches.C5), volume, int(duration_scaling*400))]

            
    

