import json
import colorama
import openai
from revChatGPT.V1 import Chatbot

from assistant.player import Player


class Chatgpt:

    def __init__(self, chatgpt_conf, chat_conf, voice_conf, config_path):
        self.chatgpt_conf = chatgpt_conf
        self.private_chatbot = None
        self.private_memory = self.chatgpt_conf["private"]["memory"]["active"]
        self.private_memory_id = self.chatgpt_conf["private"]["memory"]["id"]    
        
        self.chat_conf = chat_conf
        self.voice_conf = voice_conf
        self.config_path = config_path

        self.count = 0
        self.old_id = None


                
            
    def ask_wrapper(self, user_text):
        
        if self.chatgpt_conf["active"]:
            if self.private_memory:
                self.old_id = self.private_memory_id
            if self.old_id == "": self.old_id = None
            self.__auth_private(self.old_id)
            
                        
        if self.voice_conf["active"] == "elevenlabs":
            if self.chatgpt_conf["active"] == "private":
                if self.voice_conf["elevenlabs"]["active"] == "input_output_stream":
                    return self.__ask_private_generator(user_text)
                elif self.voice_conf["elevenlabs"]["active"] == "output_stream":
                    return self.__ask_private(user_text)
            elif self.chatgpt_conf["active"] == "official":
                if self.voice_conf["elevenlabs"]["active"] == "input_output_stream":
                    return self.__ask_official_generator(user_text)
                elif self.voice_conf["elevenlabs"]["active"] == "output_stream":
                    return self.__ask_official(user_text)
            else:
                raise Exception(self.chatgpt_conf["active"] + ": This chatgpt type does not exist")
            
        elif self.voice_conf["active"] == "google":
            if self.chatgpt_conf["active"] == "private":
                return self.__ask_private(user_text)
            elif self.chatgpt_conf["active"] == "official":
                return self.__ask_official(user_text)
            else:
                raise Exception(self.chatgpt_conf["active"] + ": This chatgpt type does not exist")
            
        else:
            raise Exception(self.voice_conf["active"] + ": This tts api type does not exist")  
            
            

    def __auth_private(self, id):
        try:
            '''
            old
            logt sich nur neu ein wenn access_token nicht vorhanden ist
            self.private_chatbot = Chatbot(config={
                "email": self.chatgpt_conf["private"]["email"],
                "password": self.chatgpt_conf["private"]["password"],
            },base_url=self.chatgpt_conf["private"]["proxy_server"] ,conversation_id=id)
            '''
            self.private_chatbot = Chatbot(config={
                "access_token": self.chatgpt_conf["private"]["access_token"]
            },base_url=self.chatgpt_conf["private"]["proxy_server"] ,conversation_id=id)

        except:
            raise Exception("ChatGPT: Private API, authentication failed")


    def __filter_text(self, text):
        # chat macht manchmal bei aufzählungen sternchen, aus vorlesung also dem return entfernen
        return text.replace("**", "")
    
    
    def __ask_private(self, text):
        
        try:
        
            old_chunk = ""
            
            """
            deprecated -> über webui von chatgpt ab jetzt
            
            #rolle hinzufügen wenn es ein neuer chat ist
            if self.count == 0:
                if self.private_memory == False:
                    text = self.chat_conf["role"] + text      
                if self.private_memory and self.old_id is None:
                    text = self.chat_conf["role"] + text
            """      

            count = 0
            for data in self.private_chatbot.ask(text):

                content = data["message"]

                if content is None or content == "": continue

                if count == 0:
                    #warte sound abspielen
                    Player.play_wait()
                    
                complete_answer = data["message"]
                chunk = data["message"]
                #remove string old_chunk in chunk
                chunk = chunk.replace(old_chunk, "")
                old_chunk = data["message"]
                count += 1
                print(chunk, end="", flush=True)

                
            print()
                
            #warte sound pausieren
            Player.play_wait_pause()
            
            self.__reset__colorama()
            
            self.count += 1

            complete_answer = self.__filter_text(complete_answer)
            return complete_answer

        
        except KeyboardInterrupt:
            raise KeyboardInterrupt
        except Exception as e:
            raise Exception("ChatGPT: private API, failed")
        finally:
            if self.private_memory:
                new_id = self.private_chatbot.conversation_id
                #if no exception occured
                if isinstance(new_id, str):
                   self.__write_private_conversation_id(new_id)




    #muss extra funktion sein. sobald yield in funktion vorkommt unabhängig ob if bedingung für yield eintrifft, wird es als generator behandelt
    def __ask_private_generator(self, text):
        
        try:
              
            old_chunk = ""
            
            """
            deprecated -> über webui von chatgpt ab jetzt
            
            #rolle hinzufügen wenn es ein neuer chat ist
            if self.count == 0:
                if self.private_memory == False:
                    text = self.chat_conf["role"] + text      
                if self.private_memory and self.old_id is None:
                    text = self.chat_conf["role"] + text
            """        

            count = 0
            for data in self.private_chatbot.ask(text):

                content = data["message"]
                
                if content is None or content == "": continue

                if count == 0:
                    #warte sound abspielen
                    Player.play_wait()
               
                chunk = data["message"]
                #remove string old_chunk in chunk
                chunk = chunk.replace(old_chunk, "")
                old_chunk = data["message"]
                count += 1
                print(chunk, end="", flush=True)
                yield chunk


                
            print()
                
            #warte sound pausieren(findet in tts statt)
            #Player.play_wait_pause()
            
            self.__reset__colorama()
            
            self.count += 1

        
        except KeyboardInterrupt:
            raise KeyboardInterrupt
        except Exception as e:
            raise Exception("ChatGPT: private API, failed")
        finally:
            if self.private_memory:
                new_id = self.private_chatbot.conversation_id
                #if no exception occured
                if isinstance(new_id, str):
                   self.__write_private_conversation_id(new_id)






    def __ask_official(self, text):
        
        try:
            openai.api_key = self.chatgpt_conf["official"]["api_key"]
            messages = [ {"role": "system", "content": self.chat_conf["role"]} ]

            messages.append(
                {"role": "user", "content": text},
            )
            complete_answer = ""
            count = 0
            for chunk in openai.ChatCompletion.create(
                model="gpt-3.5-turbo", messages=messages, stream=True
            ) :
                    content = chunk["choices"][0].get("delta", {}).get("content")

                    if content is None or content == "": continue

                    if count == 0:
                        #warte sound abspielen
                        Player.play_wait()

                    print(content, end='', flush=True)
                    complete_answer += content
                    count += 1

            print()      
            #warte sound pausieren
            Player.play_wait_pause()
            complete_answer = self.__filter_text(complete_answer)
            self.__reset__colorama()
            return complete_answer
        except KeyboardInterrupt:
            raise KeyboardInterrupt
        except Exception as e:
            raise Exception("ChatGPT: official API, failed")


    def __ask_official_generator(self, text):
        
        try:
            openai.api_key = self.chatgpt_conf["official"]["api_key"]
            messages = [ {"role": "system", "content": self.chat_conf["role"]} ]

            messages.append(
                {"role": "user", "content": text},
            )
            count = 0
            for chunk in openai.ChatCompletion.create(
                model="gpt-3.5-turbo", messages=messages, stream=True
            ) :
                    content = chunk["choices"][0].get("delta", {}).get("content")

                    if content is None or content == "": continue

                    if count == 0:
                        #warte sound abspielen
                        Player.play_wait()

                    count += 1
                    print(content, end="", flush=True)
                    yield content
                    

            print()
            #warte sound pausieren(findet in tts statt)
            #Player.play_wait_pause()
            self.__reset__colorama()

        except KeyboardInterrupt:
            raise KeyboardInterrupt
        except Exception as e:
            raise Exception("ChatGPT: official API, failed")



    def __write_private_conversation_id(self, id):

        # Schritt 1: JSON-Datei laden
        with open(self.config_path, "r", encoding="utf-8") as json_file:
            data = json.load(json_file)

        # Schritt 2: Eintrag bearbeiten
        data["chatgpt"]["private"]["memory"]["id"] = id

        # Schritt 3: Aktualisierte Daten in die JSON-Datei schreiben
        with open(self.config_path, "w", encoding="utf-8") as json_file:
            json.dump(data, json_file, indent=4, ensure_ascii=False)  
        
        #aktualisiert automatisch die conversations id der aktuellen conversation. ist ein objekt welches ein verweis ist deshalb atualisiert es auch die conversations_id im Chatbot objekt
        self.private_memory_id = id
        
         
    
    def __reset__colorama(self):
        print(colorama.Style.RESET_ALL)
