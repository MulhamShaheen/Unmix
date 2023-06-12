from djangoUnmix.settings import MEDIA_ROOT
import os


def handle_uploaded_file(file, user_id):
    folder = f'{MEDIA_ROOT}/uploads/{user_id}'
    if not os.path.exists(folder):
        os.makedirs(folder)
    with open(f'{folder}/{file.name}', 'wb+') as destination:
        for chunk in file.chunks():
            destination.write(chunk)

    return f'{folder}/{file.name}'


def handel_generated_file(file, track_id, user_id):
    folder = f'{MEDIA_ROOT}/generated/{user_id}'
    if not os.path.exists(folder):
        os.makedirs(folder)
    with open(f'{folder}/{track_id}.mp3', 'wb+') as destination:
        for chunk in file.chunks():
            destination.write(chunk)

    return f'{folder}/{track_id}.mp3'
