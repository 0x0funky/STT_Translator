import os
import streamlit as st
from pydub import AudioSegment  # Used for audio file conversion
import openai
from opencc import OpenCC

OPENAI_KEY = st.secrets["OPENAI_KEY"]

openai.api_key = OPENAI_KEY
MAX_FILE_SIZE_MB = 25

st.set_page_config(layout="wide")    

def translate(text, target_language):
    # def translate_openai(text, language):
    prompt = f"""'{text}'
    Help me to translate upper texts to {target_language}, only output target language, no need original language."""

    # Translate the chunk using the GPT model
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-16k", # engine = "deployment_name".
        messages= [{"role":"user", "content":prompt}],
        temperature = 0.5
    )
    translated_subtitles = response['choices'][0]['message']['content']
    return translated_subtitles

def process_audio(audio_file_path):
    with open(audio_file_path, 'rb') as f:
        transcribed_text = openai.Audio.transcribe("whisper-1", f, response_format="text")

    # Use your ASR tool to transcribe the audio
    # For example: transcribed_text = your_asr_tool.transcribe(audio_file_path)
    # return transcribed_text
    return transcribed_text

def save_and_convert_audio(uploaded_file):
    # Create a directory to save audio files if it doesn't exist
    if not os.path.exists('temp_audio'):
        os.makedirs('temp_audio')

    # Construct file path
    file_path = os.path.join('temp_audio', "temp_audio.mp3")

    # Save the uploaded audio file
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    # # Convert to wav if not already in that format
    # if not file_path.endswith('.wav'):
    #     sound = AudioSegment.from_file(file_path)
    #     file_path = file_path.rsplit('.', 1)[0] + '.wav'
    #     sound.export(file_path, format="wav")

    return file_path

def split_audio(file_path):
    # Split the audio file into smaller chunks
    audio = AudioSegment.from_wav(file_path)
    chunks = []
    
    chunk_length = 5 * 60 * 1000  # 5 minutes in milliseconds
    for i in range(0, len(audio), chunk_length):
        chunks.append(audio[i:i + chunk_length])
    
    return chunks

# Function to split text into smaller chunks
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

# Function to translate text and handle large text by splitting
def translate_large_text(text, target_language):
    max_token_length = 3000  # Set maximum token length for each chunk
    if len(text) > max_token_length:
        chunks = split_text(text, max_token_length)
        translated_chunks = [translate(chunk, target_language) for chunk in chunks]
        translated_text = " ".join(translated_chunks)
    else:
        translated_text = translate(text, target_language)
    return translated_text

def main():
    st.title("Audio Transcription and Translation")

    # File uploader
    audio_file = st.file_uploader("Upload Audio File (Size Limit 25MB)", type=["mp3"])

    # Dropdown for language selection
    languages = ["繁體中文"]
    target_language = st.selectbox("Select Language for Translation", languages)

    

    if st.button("Transcribe and Translate"):
        with st.spinner('Wait for it...'):
            if audio_file is not None:
                file_size_mb = len(audio_file.getvalue()) / (1024 * 1024)
                if file_size_mb > MAX_FILE_SIZE_MB:
                    st.error(f"File size exceeds the limit of {MAX_FILE_SIZE_MB} MB. Processing in chunks.")
                    
                    # Save and convert the audio file, get its path
                    audio_file_path = save_and_convert_audio(audio_file)

                    # Split the audio file
                    audio_chunks = split_audio(audio_file_path)

                    # Process each chunk and combine the transcriptions
                    full_transcription = ""
                    full_translated_text = ""
                    for chunk in audio_chunks:
                        # Save chunk as a temporary files
                        chunk_path = "temp_chunk.mp3"
                        chunk.export(chunk_path, format="mp3")

                        # Transcribe the chunk
                        transcribed_text = process_audio(chunk_path)
                        translated_text = translate_large_text(transcribed_text, target_language)
                        # translated_text = translate(transcribed_text, target_language)
                        full_transcription += transcribed_text + " "
                        full_translated_text += translated_text + " "

                    cc = OpenCC('s2twp')
                    full_translated_text = cc.convert(full_translated_text)

                    # translated_text = translate(full_transcription, target_language)

                    col1, col2 = st.columns(2)
                    with col1:
                        # Display the full transcription
                        st.text_area("Transcribed Text:", full_transcription, height=500)

                    with col2:
                        # Translate the text
                        

                        # Display translated text
                        st.text_area("Translated Text:", full_translated_text, height=500)
                else:
                    # Save and convert the audio file, get its path
                    audio_file_path = save_and_convert_audio(audio_file)

                    # Process the audio file
                    transcribed_text = process_audio(audio_file_path)


                    translated_text = translate_large_text(transcribed_text, target_language)

                    cc = OpenCC('s2twp')
                    translated_text = cc.convert(translated_text)
                    # translated_text = translate(transcribed_text, target_language)

                    col1, col2 = st.columns(2)
                    with col1:
                        # Display transcribed text
                        st.text_area("Transcribed Text:", transcribed_text, height=500)

                    with col2:
                        # Translate the text
                        

                        # Display translated text
                        st.text_area("Translated Text:", translated_text, height=500)
            else:
                st.error("Please upload an audio file.")

if __name__ == "__main__":
    main()