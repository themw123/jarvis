import io
import tempfile
import pyaudio

from pygame import mixer
from pydub import AudioSegment
from pydub.playback import play as play_pydub

from elevenlabs import stream as stream_elevenlabs
from gtts import gTTS


class Player:
    
    def __init__(self, voice_conf):
        self.voice_conf = voice_conf

    def play_wrapper(self, audio):
        if self.voice_conf["active"] == "elevenlabs":
            self.__stream_with_elevenlabs(audio)
        elif self.voice_conf["active"] == "google":
            if self.voice_conf["google"]["active"] == "stream":
                self.__stream_with_google(audio)
            elif self.voice_conf["google"]["active"] == "normal":
                self.__play_with_google(audio)
            else:
                raise Exception(self.voice_conf["google"]["active"] + ": This tts google api type does not exist")
        else:
            raise Exception(self.voice_conf["active"] + ": This tts api type does not exist")  
    
    
    
    def __stream_with_elevenlabs(self, audio_stream):
        stream_elevenlabs(audio_stream)  
                  


    def __stream_with_google(self, audio: gTTS):
        
        #damit die sprechpausen nicht so lang sind höhere buffer size
        buffer_size = 10000

        p = pyaudio.PyAudio()

        stream = p.open(format=pyaudio.paInt16,
                        channels=1,
                        rate=24000,
                        output=True,
                        frames_per_buffer=buffer_size,
                        )

        for chunk in audio.stream():
            if chunk:
                # Convert mp3 data to raw audio data
                audio = AudioSegment.from_mp3(io.BytesIO(chunk))
                audio = audio.speedup(playback_speed=1.3)
                raw_data = audio.raw_data
                stream.write(raw_data)

        stream.stop_stream()
        stream.close()
        p.terminate()
            
                
    def __play_with_google(self, audio: gTTS):
        
        tts_bytes = io.BytesIO()
        audio.write_to_fp(tts_bytes)
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        temp_file.write(tts_bytes.getvalue())
        temp_file.close()
        # AudioSegment-Objekt aus dem Inhalt erstellen
        audio = AudioSegment.from_file_using_temporary_files(temp_file.name, format="mp3")
        audio = audio.speedup(playback_speed=1.3)   
        # Audio abspielen
        play_pydub(audio)



    @staticmethod
    def play_initial():
        mixer.music.load("sound/initial.mp3")
        mixer.music.play()
            
    @staticmethod
    def play_wait():
        mixer.music.load("sound/wait.mp3")
        mixer.music.play()
    @staticmethod
    def play_wait_pause():
        mixer.music.pause()  