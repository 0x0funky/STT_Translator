import streamlit as st
from io import BytesIO
import openai
from opencc import OpenCC

OPENAI_KEY = st.secrets["OPENAI_KEY"]
openai.api_key = OPENAI_KEY
MAX_FILE_SIZE_MB = 25

st.set_page_config(layout="wide")

def translate(text, target_language):
    prompt = f"""'{text}'
    Help me to translate upper texts to {target_language}, only output target language, no need original language."""
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role":"user", "content":prompt}],
        temperature=0.5
    )
    return response['choices'][0]['message']['content']

def process_audio(audio_file):
    transcribed_text = openai.Audio.transcribe("whisper-1", audio_file, response_format="text")
    return transcribed_text

def split_text(text, max_token_length):
    words = text.split()
    chunks = []
    current_chunk = ""
    for word in words:
        if len(current_chunk) + len(word) < max_token_length:
            current_chunk += word + " "
        else:
            chunks.append(current_chunk)
            current_chunk = word + " "
    if current_chunk:
        chunks.append(current_chunk)
    return chunks

def translate_large_text(text, target_language):
    max_token_length = 3000
    if len(text) > max_token_length:
        chunks = split_text(text, max_token_length)
        translated_chunks = [translate(chunk, target_language) for chunk in chunks]
        translated_text = " ".join(translated_chunks)
    else:
        translated_text = translate(text, target_language)
    return translated_text

def main():
    st.title("Audio Transcription and Translation")

    audio_file = st.file_uploader("Upload Audio File (Size Limit 25MB)", type=["mp3"])
    target_language = st.selectbox("Select Language for Translation", ["繁體中文"])

    if st.button("Transcribe and Translate"):
        with st.spinner('Processing...'):
            if audio_file is not None:
                file_size_mb = len(audio_file.getvalue()) / (1024 * 1024)
                if file_size_mb > MAX_FILE_SIZE_MB:
                    st.error(f"File size exceeds the limit of {MAX_FILE_SIZE_MB} MB.")
                    return

                # Process the audio file
                transcribed_text = process_audio(audio_file)
                translated_text = translate_large_text(transcribed_text, target_language)

                cc = OpenCC('s2twp')
                translated_text = cc.convert(translated_text)

                col1, col2 = st.columns(2)
                with col1:
                    st.text_area("Transcribed Text:", transcribed_text, height=500)
                with col2:
                    st.text_area("Translated Text:", translated_text, height=500)
            else:
                st.error("Please upload an audio file.")

if __name__ == "__main__":
    main()