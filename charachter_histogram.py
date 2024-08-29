from pyannote.audio import Pipeline
import pandas as pd

# Load API token
df = pd.read_csv('api_token.csv')
api_key = df['hf'].iloc[0]

pipeline = Pipeline.from_pretrained(
    "pyannote/speaker-diarization-3.1",
    use_auth_token=api_key)

# send pipeline to GPU (when available)
#import torch
#pipeline.to(torch.device("cuda"))

# apply pretrained pipeline
diarization = pipeline("source/audio.mp3")

# print the result
for turn, _, speaker in diarization.itertracks(yield_label=True):
    print(f"start={turn.start:.1f}s stop={turn.end:.1f}s speaker_{speaker}")