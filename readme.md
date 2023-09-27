# Jarvis

Jarvis ist ein Konsolen-Assistent mit dem man eine Unterhaltung über alles mögliche führen kann.


https://github.com/themw123/jarvis/assets/80266862/4df23ed3-3ea9-4900-b2dc-51526ecb0b2f


Folgende Features sind enthalten und können über die config.json eingestellt werden:

- Voice To Text 📝:
    - Whisper(api key erforderlich, kostet)
    - Google(ohne key, kostenlos)

- response AI 🧠:
    - ChatGPT(official api, kostet oder private api kostenlos)

- Text to Speech 💬:
    - Elevenlabs(api key erforderlich, kostet. input_output_stream oder output_stream) -> Proxy support✔️
    - Google(ohne key, kostenlos. stream oder normal)

Best practise hat man mit Whisper und Elevenlabs(input_output_stream -> Text von ChatGPT wird während der Generierung an Elevenlabs geschickt und währenddessen step by step abgespielt mittels WebSocket).


Es müssen folgende programme installiert werden, damit der Asssistent läuft:

1. https://ffmpeg.org/
2. https://mpv.io/

Die Programme müssen über Umgebungsvariablen verfügbar gemacht werden.




Update:

Da die zugrunde liegende private api von ChatGPT nicht mehr gewartet wird, muss nun der access_token selber gesetzt werden in:
```
 C:\Users\%USERNAME%\.config\revChatGPT\cache.json
```
Den Token bekommt man unter
```
https://chat.openai.com/api/auth/session
```
Der Token ist für rund einen Monat gültig und muss dann erneut gesetzt werden.


