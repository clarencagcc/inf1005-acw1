import librosa
import librosa.display
import matplotlib.pyplot as plt
import numpy as np
import io

def plot_spectrogram(wav_file):
    # Load the WAV file using librosa
    y, sr = librosa.load(wav_file, sr=None)

    # Create a spectrogram using librosa
    S = librosa.feature.melspectrogram(y=y, sr=sr)
    S_dB = librosa.power_to_db(S, ref=np.max)

    # Plot the spectrogram
    fig, ax = plt.subplots(figsize=(10, 2))
    img = librosa.display.specshow(S_dB, sr=sr, x_axis='time', y_axis='mel', ax=ax)
    fig.colorbar(img, ax=ax, format="%+2.0f dB")

    # Save the spectrogram to a BytesIO buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close(fig)
    
    return buf

