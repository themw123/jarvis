
import json
import colorama

#contextlib um "hello from the pygame community" zu entfernen
import contextlib
with contextlib.redirect_stdout(None):
    from pygame import mixer
    
from assistant.recorder import Recorder
from assistant.player import Player
from assistant.vtt import Vtt
from assistant.tts import Tts
from assistant.chatgpt import Chatgpt


def main():

    print("\n- start assistant...\n")

    read_conf()
    colorama.init()
    mixer.init()
    
    recorder = Recorder()
    player = Player(voice_conf)
    
    chatgpt = Chatgpt(chatgpt_conf, chat_conf, voice_conf, config_path)

    vtt = Vtt(recognition_conf, chatgpt_conf)
    tts = Tts(voice_conf)
    

    #Begrüßung starten
    Player.play_initial()
    
    
    while True:

        try:
            audio = recorder.listen()
            user_text = vtt.vtt_wrapper(audio=audio)
            print_user(user_text)
            #user_text = input("(User): ")
            #user_text = "schreibe mir ein langes gedicht"
            
            print_assistant()
            chatgpt_text = chatgpt.ask_wrapper(user_text=user_text)
  
            audio = tts.tts_wrapper(chatgpt_text=chatgpt_text)
            player.play_wrapper(audio=audio)
  
 
        except KeyboardInterrupt:
            
            print(colorama.Style.RESET_ALL)
            mixer.music.pause()
            continue
        


            
def read_conf():
    
    global config_path
    config_path = "config.json"
    
    with open(config_path, 'r') as f:
        config = json.load(f)
        
        
    global chat_conf, chatgpt_conf
    chat_conf = config["chat"]
    chatgpt_conf = config["chatgpt"]

    global recognition_conf
    recognition_conf = config["recognition"]
        
    global voice_conf
    voice_conf = config["voice"]
        
  

def print_user(user_text):
    print("\n" + colorama.Fore.YELLOW + "("+ chat_conf["your_name"] +"):", user_text + colorama.Style.RESET_ALL)

def print_assistant():
    print("\n" + colorama.Fore.GREEN + "("+chat_conf["role_name"]+"): ", end="")        



if __name__ == "__main__":
    main()
   


