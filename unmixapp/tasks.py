import string

import torch
from django.contrib.auth.models import User
from django.utils.crypto import get_random_string
from unmixapp.unet import UNet
from .models import Track
from .functions import handle_uploaded_file, handel_generated_file
from unmixapp import UVocalController, UBassController, URestController, UDrumsController, audioController

from celery import shared_task

CONTROLLERS = {
    "VOCAL": UVocalController,
    "BEAT": UDrumsController,
    "BASS": UBassController,
    "OTHER": URestController,
}


@shared_task
def process_track(upload_path, result_path, track_id, instrument):
    stft_array = audioController.generate_spectro(audiofile=upload_path, crop=48)
    controller = CONTROLLERS[instrument]
    pred_array = []
    result_stft = torch.tensor([])
    for stft in stft_array:
        pred_mask = controller.predict(stft, )
        pred_stft = audioController.apply_mask(stft, pred_mask)
        result_stft = torch.cat((result_stft, pred_stft), dim=1)

    audio = audioController.generate_audio(result_stft, result_path)

    track = Track.objects.get(pk=track_id)
    track.status = "DONE"
    track.save()


@shared_task
def test_task():
    print("Done!")
    return 1
