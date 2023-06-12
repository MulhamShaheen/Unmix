import os
import numpy as np
import librosa
import torch
from .unet import UNet
# from ipywidgets import Audio
from IPython.display import Audio


class AudioProcessor:
    def __init__(self, sample_rate=44100, n_fft=2047, hop_length=517):
        self.sample_rate = sample_rate
        self.n_fft = n_fft
        self.hop_length = hop_length

    def generate_spectro(self, audiofile, crop: int = 48, target_shape=(1, 1024, 4096)):
        y, sr = librosa.load(audiofile, sr=44100)
        self.sample_rate = sr
        index = 0
        stft_array = []
        while len(y) - index > 48 * sr:
            # if len(y) - index < 48*sr:
            #
            #     break
            x = y[index:index + crop * sr + 1]
            stft = librosa.stft(x, n_fft=self.n_fft, hop_length=self.hop_length, )
            stft = np.abs(stft)
            stft = torch.FloatTensor(stft)
            shape = stft.shape
            if shape[1] != target_shape[2]:
                pad = torch.nn.ConstantPad1d((0, target_shape[2] - shape[1]), 0)
                stft = pad(stft)
                shape = stft.shape

            stft = stft.unsqueeze(0)
            stft_array.append(stft)
            index = index + crop * sr + 1
        return stft_array

    @staticmethod
    def apply_mask(stft, mask):
        result = stft[0] * mask[0][0]

        return result

    def generate_audio(self, stft, track_path):
        stft = stft.numpy()
        y_inv = librosa.griffinlim(stft)
        audio = Audio(data=y_inv, rate=self.sample_rate)

        with open(track_path, 'wb') as f:
            f.write(audio.data)


class UnetController:
    def __init__(self, input_length=14,
                 sample_rate=44100,
                 in_channels=1,
                 out_channels=1,
                 n_blocks=1,
                 start_filters=8,
                 activation='relu',
                 trained_model="unet/bass.pt"
                 ):
        self.input_length = input_length
        self.sample_rate = sample_rate
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.n_blocks = n_blocks
        self.start_filters = start_filters
        self.activation = activation
        self.trained_model = trained_model

        self.model = UNet(in_channels=self.in_channels,
                          out_channels=self.out_channels,
                          n_blocks=self.n_blocks,
                          start_filters=self.start_filters, )

        if self.trained_model is not None:
            states = torch.load(self.trained_model, map_location=torch.device('cpu'))
            self.model.load_state_dict(states)

        self.model.eval()

    def predict(self, stft: torch.Tensor):
        stft = stft.unsqueeze(0)
        pred_mask = self.model.forward(stft).detach()
        pred_mask = torch.relu(torch.sign(torch.sigmoid(pred_mask) - 0.5))
        return pred_mask
