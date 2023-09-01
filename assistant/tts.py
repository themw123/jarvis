import json
import base64
import threading
import time
import colorama
import requests
import queue

import websocket
from elevenlabs.api.tts import text_chunker 
from gtts import gTTS

from assistant.player import Player




class Tts:
    
    thread_exceptions = []
    voice_settings = None
    
    @staticmethod
    def on_open(wsapp):
        #body
        BOS = json.dumps(
            dict(
                text=" ",
                try_trigger_generation=True,
                voice_settings=voice_settings,
                generation_config=dict(
                    chunk_length_schedule=[50],
                ),
            )
        )
        wsapp.send(BOS)
    
    @staticmethod
    def on_message(wsapp, message):
        #print("!Nachricht erhalten!")
        #print(message)  
        data = json.loads(message)
        if data["audio"]:
            #warte sound pausieren
            Player.play_wait_pause()
            tospeak = base64.b64decode(data["audio"])  # type: ignore
            Tts.audio_queue.put(tospeak)

    @staticmethod
    def on_close(wsapp, close_status_code, close_msg):
        #print("Output stream ENDE")
        if close_status_code != 1000:
            error = {
                "function": "on_close",
                "msg": close_msg
            }
            Tts.thread_exceptions.append(error)
        Tts.audio_queue.put("end_of_output_stream")

    @staticmethod        
    def on_error(wsapp, error):
        #print(error)
        myerror = {
            "function": "on_error",
            "msg": error
        }
        #thread_exceptions.append(myerror)
        Tts.audio_queue.put("end_of_output_stream")





    def __init__(self, voice_conf):
        
        self.voice_conf = voice_conf
        
        global voice_settings
        voice_settings = dict(stability=self.voice_conf["elevenlabs"]["settings"]["stability"], similarity_boost=self.voice_conf["elevenlabs"]["settings"]["similarity_boost"])
        
    def tts_wrapper(self, chatgpt_text):
        if self.voice_conf["active"] == "elevenlabs":
            if self.voice_conf["elevenlabs"]["active"] == "input_output_stream":
                return self.__tts_elevenlabs_input_output_stream(chatgpt_text)
            elif self.voice_conf["elevenlabs"]["active"] == "output_stream":
                return self.__tts_elevenlabs_output_stream(chatgpt_text)
            else:
                raise Exception(self.voice_conf["active"] + ": This elevenlabs type does not exist")  
        elif self.voice_conf["active"] == "google":
            return self.__tts_google(chatgpt_text)
        else:
            raise Exception(self.voice_conf["active"] + ": This tts api type does not exist")  

        
    def __tts_elevenlabs_input_output_stream(self, text):  
        
        url = "wss://api.elevenlabs.io/v1/text-to-speech/"+ self.voice_conf["elevenlabs"]["id"] +"/stream-input?model_id=" + self.voice_conf["elevenlabs"]["lingual"]
        

        #header
        header = {"xi-api-key": self.voice_conf["elevenlabs"]["key"]}
        
        #websocket.enableTrace(True)
        ws = websocket.WebSocketApp(url, header=header, on_open=Tts.on_open, on_message=Tts.on_message, on_close=Tts.on_close, on_error=Tts.on_error)
        #Starte die WebSocket-Kommunikation in einem separaten Thread und empfange daten in diesm Thread
        
        kwargs = {}
        if self.voice_conf["elevenlabs"]["proxy"]["active"] == True:
            kwargs = {
                "proxy_type": self.voice_conf["elevenlabs"]["proxy"]["type"],
                "http_proxy_host": self.voice_conf["elevenlabs"]["proxy"]["url"],
                "http_proxy_port": self.voice_conf["elevenlabs"]["proxy"]["port"],
                "http_proxy_auth": (self.voice_conf["elevenlabs"]["proxy"]["username"], self.voice_conf["elevenlabs"]["proxy"]["password"])
            }
            
        websocket_thread = threading.Thread(target=ws.run_forever, kwargs={**kwargs}, name="websocket_thread")  
        websocket_thread.start()

        #sende chunks hinein(non-blocking)
        stream_input = threading.Thread(target=self.__stream_input, args=(ws, text), name="stream_input")
        stream_input.start()
        

        #muss unbedingt hier erfolgen, damit bei keyboard interruption und der darauf folgenden iteration nicht die alte audio verwendet wird.
        Tts.audio_queue = queue.Queue()
        #hole audio chunks aus queue und gebe audio zurück in chunks.
        while True:
            data = Tts.audio_queue.get(block=True)
            if data == "end_of_output_stream":
                break
            yield data
    

        websocket_thread.join()
        stream_input.join()
        #Überprüfen und verarbeiten Sie Ausnahmen aus websocket Thread
        if Tts.thread_exceptions:
            print(colorama.Style.RESET_ALL + "Exceptions:")
            Player.play_wait_pause()
            for exception in Tts.thread_exceptions:
                print(exception["function"]+": "+ str(exception["msg"]))
                if "This request exceeds your quota" in str(exception["msg"]):
                    print("- This request exceeds your quota...")

                    
            print()
            #get um queue zu leeren
            Tts.audio_queue.get()
            Tts.thread_exceptions.clear()


        


    def __stream_input(self, ws, text):
        try:
            # input stream text chunks
            for text_chunk in text_chunker(text):
                data = dict(text=text_chunk, try_trigger_generation=True)
                ws.send(json.dumps(data))    
            
            #bricht wohl auch schon direkt am anfang hier raus. Aber End EOS kann und muss gesendet werden. Socket schließt trotzdem erst nachdem alle Antworten gesendet wurden.

            # Send end
            #dadurch wird bei websocket server von elevenlabs die verbindung geschlossen. Das triggert dann das on_close event.
            #print("!Input stream ENDE!")
            #body
            EOS = json.dumps(dict(text=""))
            ws.send(EOS)
            
        except Exception as e:
            error = {
                "function": "__stream_input",
                "msg": e
            }
            #thread_exceptions.append(error)





    def __tts_elevenlabs_output_stream(self, text):  
        

        url = "https://api.elevenlabs.io/v1/text-to-speech/"+ self.voice_conf["elevenlabs"]["id"] +"/stream"


        data = {
        "text": text,
        "model_id": self.voice_conf["elevenlabs"]["lingual"],
            "voice_settings": voice_settings
        }
        

        while True:
        

            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.voice_conf["elevenlabs"]["key"]
            }

            proxies = None
            if self.voice_conf["elevenlabs"]["proxy"]["active"] == True:
                proxy_url = f"{self.voice_conf['elevenlabs']['proxy']['url']}:{self.voice_conf['elevenlabs']['proxy']['port']}"
                proxies = {
                    "http": f"http://{self.voice_conf['elevenlabs']['proxy']['username']}:{self.voice_conf['elevenlabs']['proxy']['password']}@{proxy_url}",
                    "https": f"http://{self.voice_conf['elevenlabs']['proxy']['username']}:{self.voice_conf['elevenlabs']['proxy']['password']}@{proxy_url}",
                }
                    
            try:
                response = requests.post(url, json=data, headers=headers, stream=True, proxies = proxies)
            except Exception as e:
                raise Exception("Elevenlabs: Request error")
            

            if response.status_code != 200:
                text = None
                
                if "Unusual activity detected" in response.json()["detail"]["message"]:
                    if self.voice_conf["elevenlabs"]["proxy"]["active"]:
                        raise Exception("despite proxy, unusual activity detected.")
                    else:
                        raise Exception("unusual activity detected. Try with Proxy.")
                         
                if "This request exceeds your quota" in response.json()["detail"]["message"]:
                    print("\n- This request exceeds your quota")
                    print()
                else:
                    raise Exception(f"Unexpected response received. Status code: {response.status_code}, body: {response.content}")
                
            else:
                break
            


        return response
    
    
    def __tts_google(self, chatgpt_text):
        return gTTS(text=chatgpt_text, lang=self.voice_conf["google"]["language"], slow=False)
    
    
    def __print_public_ip(self):
        
        response = requests.get('https://api64.ipify.org?format=json')
        data = response.json()
        print(data['ip'])
    
        proxy_url = f"{self.voice_conf['elevenlabs']['proxy']['url']}:{self.voice_conf['elevenlabs']['proxy']['port']}"
        proxies = {
            "http": f"http://{self.voice_conf['elevenlabs']['proxy']['username']}:{self.voice_conf['elevenlabs']['proxy']['password']}@{proxy_url}",
            "https": f"http://{self.voice_conf['elevenlabs']['proxy']['username']}:{self.voice_conf['elevenlabs']['proxy']['password']}@{proxy_url}",
        }
        
        response = requests.get('https://api64.ipify.org?format=json', proxies = proxies)
        data = response.json()
        print(data['ip'])


