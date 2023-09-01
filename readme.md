# Jarvis

Jarvis ist ein konsolen Assistent mit dem man eine Unterhaltung über alles mögliche führen kann.
Folgende Features sind enthalten und können über die config.json eingestellt werden:

- Voice To Text 📝:
    - Whisper(api key erforderlich, kostet)
    - Google(ohne key, kostenlos)

- response AI 🧠:
    - ChatGPT

- Text to Speech 💬:
    - Elevenlabs(api key erforderlich, kostet. input_output_stream oder output_stream)
    - Google(ohne key, kostenlos. stream oder normal)

Best practise hat man mit Whisper und Elevenlabs(input_output_stream -> Text von ChatGPT wird während der Generierung an Elevenlabs geschickt und währenddessen step by step abgespielt mittels WebSocket).


Es müssen folgende programme installiert werden, damit der Asssistent läuft:

1. https://ffmpeg.org/
2. https://mpv.io/

Die Programme müssen über Umgebungsvariablen verfügbar gemacht werden.

