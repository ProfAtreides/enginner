import torch, torchaudio
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
from pyannote.audio import Pipeline
import pandas as pd
from pydub import AudioSegment
import io
import numpy as np
import decimal
import os
import subprocess

def translate_speech(audio):
    device = "cuda:0" if torch.cuda.is_available() else "cpu"

    if device == "cuda:0":
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.allow_tf32 = True

    print(f"Using device: {device}")

    torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

    model_id = "openai/whisper-large-v3"

    model = AutoModelForSpeechSeq2Seq.from_pretrained(
        model_id, torch_dtype=torch_dtype, low_cpu_mem_usage=True, use_safetensors=True
    )
    model.to(device)

    processor = AutoProcessor.from_pretrained(model_id)

    pipe = pipeline(
        "automatic-speech-recognition",
        model=model,
        tokenizer=processor.tokenizer,
        feature_extractor=processor.feature_extractor,
        torch_dtype=torch_dtype,
        device=device,
    )

    samples = sample_audio(audio)

    subtitles = []

    # Transcribe audio samples
    for start,end, sample in samples:
        result = pipe(sample)
        print(result["text"])
        subtitles.append({"start":start/1000.0,"end":end/1000.0,"text":result["text"]})
    return subtitles



def create_histogram(file_path,num_speakers):
    df = pd.read_csv("api_token.csv")
    api_key = df["hf"].iloc[0]

    temp_file = "temp.wav"

    pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization-3.1",
        use_auth_token=api_key
    )

    try:
        # Run the ffmpeg command
        subprocess.run(
            ["ffmpeg", "-i", file_path, "-q:a", "0", "-map", "a", temp_file],
            check=True
        )
    except subprocess.CalledProcessError as e:
        raise Exception(f"Error during conversion: {e}")


    pipeline.to(torch.device("cuda" if torch.cuda.is_available() else "cpu"))

    waveform, sample_rate = torchaudio.load("source/input.wav")

    diarization = pipeline({"waveform": waveform, "sample_rate": sample_rate}, num_speakers=num_speakers)

    histogram = []
    colors = ["white", "blue", "green", "yellow", "purple", "orange"]
    for i, (turn, _, speaker) in enumerate(diarization.itertracks(yield_label=True)):
        color = colors[int(speaker[-1])]
        
        if len(histogram) == 0:
            histogram.append({"start":0, "end":turn.start, "color":"white"})
            continue
        
        if histogram[-1]["color"] == color:
            histogram[-1]["end"] = turn.start
        else :
            histogram[-1]["end"] = turn.start
            histogram.append({"start":turn.start, "end":turn.end, "color":color})
        
    try:
        if os.path.exists(temp_file):
            os.remove(temp_file)
            print(f"Deleted file: {temp_file}")
        else:
            print(f"File not found: {temp_file}")
    except Exception as e:
        print(f"Error during file deletion: {e}")
        
    return histogram


def extract_audio_from_mp4(input_path):
    """
    Extracts audio from an MP4 video file.
    """
    audio = AudioSegment.from_file(input_path, format="mp4")
    return audio


def sample_audio(raw_audio):
    
    audio_samples = [] # Also has time
    
    vid_duration = raw_audio.duration_seconds
    
    for time in np.arange(0,vid_duration,10.0):
        start_time = time * 1000
        end_time = (time + 10.0) * 1000 if time+ 10.0 <= vid_duration else vid_duration * 1000
        sample = raw_audio[start_time: end_time] 
        audio = io.BytesIO()
        sample.export(audio, format="wav")
        audio.seek(0)
        audio_samples.append((start_time,end_time,audio.read()))
    return audio_samples

def eng_to_pol(dialogues):
    from deep_translator import DeeplTranslator
    import pandas as pd
    
    df = pd.read_csv('api_token.csv')
    api_key = df['deepl'].iloc[0]
    
    for dialogue in dialogues:
        translation = (DeeplTranslator(api_key=api_key, source='english', target='polish').translate(dialogue["text"]))
        dialogue["text"] = translation
        print(translation)
            
    return dialogues
    