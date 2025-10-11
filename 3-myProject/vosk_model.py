import sounddevice as sd
import queue
import json
from vosk import Model, KaldiRecognizer


class VoskRecognizer:
    def __init__(self, model_path: str, samplerate: int = 16000):
        self.model = Model(model_path)
        self.recognizer = KaldiRecognizer(self.model, samplerate)
        self.q = queue.Queue()
        self.samplerate = samplerate

    def _callback(self, indata, frames, time, status):
        if status:
            print(status)
        self.q.put(bytes(indata))

    def listen(self):
        print("🎙️ Dinleniyor (Ctrl+C ile çık)")
        with sd.RawInputStream(samplerate=self.samplerate, blocksize=8000,
                               dtype='int16', channels=1, callback=self._callback):
            while True:
                data = self.q.get()
                if self.recognizer.AcceptWaveform(data):
                    result = json.loads(self.recognizer.Result())
                    text = result.get("text", "")
                    if text:
                        print("🗣️", text)
                else:
                    partial = json.loads(self.recognizer.PartialResult())
                    if partial.get("partial"):
                        print("⌛", partial["partial"], end="\r")

if __name__ == "__main__":
    model_path = "vosk-model-small-tr-0.3"
    vr = VoskRecognizer(model_path)
    vr.listen()
