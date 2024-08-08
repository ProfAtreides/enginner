import os
import numpy as np
import pandas as pd
from pyannote.audio import Inference, Model
from pyannote.audio.pipelines import SpeakerDiarization
from pyannote.metrics.diarization import DiarizationErrorRate

def compare_voices(reference_embedding, target_audio):
    target_embedding = embedding_inference(target_audio)
    distance = np.linalg.norm(reference_embedding - target_embedding)
    return distance

# Load API token
df = pd.read_csv('api_token.csv')
api_key = df['hf'].iloc[0]

# Load pre-trained embedding model
embedding_model = Model.from_pretrained("pyannote/embedding",
                                        use_auth_token=api_key)
embedding_inference = Inference(embedding_model, window="whole")

# Load pre-trained diarization model
diarization_pipeline = SpeakerDiarization.from_pretrained("pyannote/speaker-diarization",
                                                          use_auth_token=api_key)

# Reference audio file
reference_audio = "source/input.wav"

# Compute embedding for the reference audio
reference_embedding = embedding_inference(reference_audio)
# Diarization on the target audio file
target_audio = "source/input.wav"
diarization_result = diarization_pipeline(target_audio)

# Define a threshold for similarity
threshold = 0.0

# Iterate over the diarization result to extract segments and compare embeddings
for turn, _, speaker in diarization_result.itertracks(yield_label=True):
    segment_audio = f"{speaker}_{turn.start:.1f}-{turn.end:.1f}.wav"

    # Extract the segment using ffmpeg
    command = f"ffmpeg -i {target_audio} -ss {turn.start:.1f} -to {turn.end:.1f} -c copy {segment_audio} -y"
    os.system(command)

    # Compare the voice in the segment with the reference voice
    similarity = compare_voices(reference_embedding, segment_audio)
    if similarity < threshold:
        print(f"The reference speaker speaks from {turn.start:.1f}s to {turn.end:.1f}s")

    # Clean up the segment audio file
    os.remove(segment_audio)
