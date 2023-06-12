import torch
from django.conf import settings
from djangoUnmix.settings import MEDIA_ROOT
from django.contrib.auth import authenticate, login
from django.contrib.auth import logout as _logout
from django.http import HttpResponse, Http404
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from .forms import CustomUserCreationForm, TrackUploadForm, FeedbackForm
from .models import User, Track, Feedback
from .functions import handle_uploaded_file, handel_generated_file
from .controllers import UnetController, AudioProcessor

from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.parsers import JSONParser
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authentication import TokenAuthentication
from django.views.decorators.csrf import csrf_exempt
from rest_framework.authtoken.models import Token
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import *
from .tasks import process_track

UBassController = UnetController(trained_model=None)
audioController = AudioProcessor()


def sign_in(request):
    if request.method == 'POST':
        email = request.POST["email"]
        password = request.POST["password"]
        user = authenticate(request, username=email, password=password)
        print(user)
        if user is not None:
            login(request, user)
            return redirect("home")
        else:
            return redirect("login")

    else:
        return render(request, "unmixapp/signin.html")


@csrf_exempt
def sign_up(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            new_user = form.save(commit=True)
            login(request, new_user)
            return redirect("home")

        return redirect("sign_up")

    else:
        return render(request, 'unmixapp/signup.html')


def index(request):
    if request.method == 'POST' and request.FILES['uploaded_file']:
        uploaded_file = request.FILES['uploaded_file']

        return render(request, 'unmixapp/index.html', {
            'res': "pass",
            'file_name': uploaded_file.name
        })

    if request.user.is_authenticated:
        context = {
            'user': request.user.email,
            'data': "sadasd",
        }
        return render(request, 'unmixapp/index.html', context)

    context = {
        'user': 'unauthenticated',
    }
    return render(request, 'unmixapp/index.html', context)


def main(request):
    if not request.user.is_authenticated:
        return redirect('login')

    form = TrackUploadForm()
    context = {
        'form': form,
        'data': None,
        'user': request.user,
    }

    if request.method == "GET":
        return render(request, 'unmixapp/main.html', context)

    elif request.method == "POST":
        data = request.POST
        file = request.FILES['file']
        extension = file.name.split(".")[-1]
        if extension != 'wav' and extension != 'mp3':
            context['success'] = False
            context['error'] = "File should be wav or mp3"
            return render(request, 'unmixapp/main.html', context)

        track = Track.objects.create(
            instrument=data['target_instrument'],
            user_id=request.user,
        )

        upload_path = handle_uploaded_file(file, request.user.id)
        result_path = handel_generated_file(file, track.id, request.user.id)

        track.upload_path = upload_path
        track.result_path = result_path
        user = request.user

        process_track.delay(upload_path, result_path, track_id=track.id, instrument=data['target_instrument'])

        track.save()

        context['data'] = data
        context['success'] = True
        return render(request, 'unmixapp/main.html', context)


def profile(request):
    if not request.user.is_authenticated:
        return redirect('login')

    user = request.user
    tracks = Track.objects.filter(user_id=user.id).order_by('-created_at', )

    return render(request, 'unmixapp/profile.html', {'tracks': tracks})


def feedback(request, track_id):
    if not request.user.is_authenticated:
        return redirect('login')

    user = request.user
    track = Track.objects.get(pk=track_id)
    if request.method == 'POST':
        feed = Feedback(user_id=user, track_id=track, )
        form = FeedbackForm(request.POST, instance=feed)
        if form.is_valid():
            form.save()
            return redirect('profile')

        return redirect(request.path_info, {"error": "score should be from 0 to 10"})

    feed = Feedback(user_id=user, track_id=track, text=" ", score=5)
    form = FeedbackForm(instance=feed)

    return render(request, 'unmixapp/feedback.html', {'track': track, 'form': form})


def logout(request):
    _logout(request)

    return redirect("login")


class Authorization(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        data = JSONParser().parse(request)

        email = data['email']
        password = data['password']
        user = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user)
            refresh = RefreshToken.for_user(user)

            return Response({
                'data': str(user),
                'refresh': str(refresh),
                'access': str(refresh.access_token),

            }, status=200)

        else:
            return Response({"msg": "invalid login"}, status=400)


class TracksView(APIView):
    def get(self, request, id=None):
        user = request.user
        if id is None:
            tracks = Track.objects.filter(user_id=user)
            many = True

        else:
            tracks = Track.objects.get(id=id)
            many = False
            if user.id != tracks.user_id.id:
                return Response({'errors': 'Forbidden'}, status=403)

        serializer = TrackSerializer(tracks, many=many)
        return Response(serializer.data, status=201)

    def put(self, request):
        user = request.user
        data = JSONParser().parse(request['PUT'])
        data['user_id'] = user
        file = request['FILES']
        serializer = TrackSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        else:
            return Response(serializer.errors, status=400)


def download(request, track_id):
    track = Track.objects.get(pk=track_id)
    file_path = os.path.join(MEDIA_ROOT, f"generated/{request.user.id}/{track_id}.mp3")
    if os.path.exists(file_path):
        with open(file_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/file")
            response['Content-Disposition'] = f'inline; filename={track.instrument}_{os.path.basename(track.upload_path)}'
            return response
    raise Http404

