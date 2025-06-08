import os
from groq import Groq
from pathlib import Path
import speech_recognition as sr
import pyttsx3
import sys
import io
from pydub import AudioSegment
from playsound import playsound
r = sr.Recognizer()


chat_history = [
    {"role": "system", "content": "you are a voice assistant. answer briefly"}
]


def test_microphone():
    """Test if microphone is available"""
    try:
        with sr.Microphone() as source:
            print("Microfone detectado com sucesso!")
            return True
    except Exception as e:
        print(f"Erro ao acessar microfone: {e}")
        return False

def record_text():
    """Record audio and convert to text"""
    try:
        # Use microphone as input source
        with sr.Microphone() as source:
            print("Ajustando para ruído ambiente...")
            # Prepare recognizer to receive input
            r.adjust_for_ambient_noise(source, duration=0.2)
            print("Ouvindo... Fale agora!")
            
            # Listen for input
            audio_data = r.listen(source, timeout=5, phrase_time_limit=10)
            print("Processando áudio...")
            sample_rate = audio_data.sample_rate
            sample_width = audio_data.sample_width
            channels = 1  # Geralmente, o áudio capturado é mono

            # Crie um objeto AudioSegment a partir dos dados brutos
            audio_segment = AudioSegment(
                data=audio_data.get_raw_data(),
                sample_width=sample_width,
                frame_rate=sample_rate,
                channels=channels
            )

            # Exporte para MP3
            audio_segment.export("saida.m4a", format="mp4", codec="aac")

            MyText = r.recognize_google(audio_data) 
            print(f"Texto reconhecido: {MyText}")
            return MyText

    except sr.WaitTimeoutError:
        print("Timeout - nenhum áudio detectado")
        return None
    except sr.RequestError as e:
        print(f"Erro na requisição ao Google: {e}")
        return None
    except sr.UnknownValueError:
        print("Google não conseguiu entender o áudio")
        return None
    except Exception as e:
        print(f"Erro inesperado: {e}")
        return None

def output_text(text):
    chat_history.append({"role": "user", "content": text})
    client = Groq(api_key='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')
    completion = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=chat_history,
        temperature=1,
        max_completion_tokens=1024,
        top_p=1,
        stream=True,
        stop=None,
    )
    """
        resposta_do_gpt+ str(chunk.choices[0].delta.content)
    """
    resposta_do_str:str=""
    for chunk in completion:
        resposta_do_str+=(chunk.choices[0].delta.content or "")
    print("resposta do gpt: "+str(resposta_do_str))

    chat_history.append({"role": "assistant", "content": resposta_do_str})
    speech_file_path = Path(__file__).parent / "speech.mp3"
    response = client.audio.speech.create(
    model="playai-tts",
    voice="Aaliyah-PlayAI",
    response_format="mp3",
    input=resposta_do_str,
    )
    
    response.write_to_file(speech_file_path)

    playsound(speech_file_path, block=True)

def main():
    """Main function"""
    print("=== Reconhecimento de Voz ===")
    
    # Test microphone first
    if not test_microphone():
        print("Erro: Não foi possível acessar o microfone.")
        print("Verifique se:")
        print("1. O microfone está conectado")
        print("2. As permissões estão corretas")
        print("3. O PulseAudio está funcionando")
        sys.exit(1)
    
    print("Pressione Ctrl+C para parar")
    
    try:
        while True:
            text = record_text()
            if text:
                output_text(text)
            else:
                print("Tentando novamente...")
                
    except KeyboardInterrupt:
        print("\nPrograma interrompido pelo usuário.")
    except Exception as e:
        print(f"Erro fatal: {e}")

if __name__ == "__main__":
    main()