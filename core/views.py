from django.shortcuts import render, HttpResponse, redirect,get_object_or_404
from .models import *
from .forms import *
import face_recognition
import cv2
import numpy as np 
import winsound
from django.db.models import Q
import os
import time 
from .models import UnknownFace
from django.views import View
from django.core.files.storage import default_storage

last_face = 'no_face'
current_path = os.path.dirname(__file__)
sound_folder = os.path.join(current_path, 'sound/')
face_list_file = os.path.join(current_path, 'face_list.txt')
sound = os.path.join(sound_folder, 'beep.wav')


def index(request):
    scanned = LastFace.objects.all().order_by('date').reverse()
    present = Profile.objects.filter(present=True).order_by('updated').reverse()
    absent = Profile.objects.filter(present=False).order_by('shift')
    context = {
        'scanned': scanned,
        'present': present,
        'absent': absent,
    }
    return render(request, 'core/index.html', context)


def ajax(request):
    last_face = LastFace.objects.last()
    context = {
        'last_face': last_face
    }
    return render(request, 'core/ajax.html', context)


def scan(request):
    unknown_face_count = 1
    global last_face

    known_face_encodings = []
    known_face_names = []

    profiles = Profile.objects.all()
    for profile in profiles:
        person = profile.image
        image_of_person = face_recognition.load_image_file(f'media/{person}')
        person_face_encoding = face_recognition.face_encodings(image_of_person)[0]
        known_face_encodings.append(person_face_encoding)
        known_face_names.append(f'{person}'[:-4])

    video_capture = cv2.VideoCapture(0)

    face_locations = []
    face_encodings = []
    face_names = []
    process_this_frame = True

    while True:

        ret, frame = video_capture.read()
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = small_frame[:, :, ::-1]

        if process_this_frame:
            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_encodings = face_recognition.face_encodings(
                rgb_small_frame, face_locations)

            face_names = []
            for face_encoding in face_encodings:
                matches = face_recognition.compare_faces(
                    known_face_encodings, face_encoding)
                name = "Unknown"

                face_distances = face_recognition.face_distance(
                    known_face_encodings, face_encoding)
                best_match_index = np.argmin(face_distances)
                if matches[best_match_index]:
                    name = known_face_names[best_match_index]

                    profile = Profile.objects.get(Q(image__icontains=name))
                    if profile.present == True:
                        pass
                    else:
                        profile.present = True
                        profile.save()

                    if last_face != name:
                        last_face = LastFace(last_face=name)
                        last_face.save()
                        last_face = name
                        winsound.PlaySound(sound, winsound.SND_ASYNC)
                    else:
                        pass
 
                face_names.append(name)

        process_this_frame = not process_this_frame

        for (top, right, bottom, left), name in zip(face_locations, face_names):
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4

            cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

            cv2.rectangle(frame, (left, bottom - 35),
                          (right, bottom), (0, 0, 255), cv2.FILLED)
            font = cv2.FONT_HERSHEY_DUPLEX
            cv2.putText(frame, name, (left + 6, bottom - 6),
                        font, 0.5, (255, 255, 255), 1)

            if name == "Unknown":
                # Capture and save the screenshot for the unknown face
                save_unknown_face_screenshot(frame, top, right, bottom, left)

        cv2.imshow('Video', frame)

        if cv2.waitKey(1) & 0xFF == 13:
            break

    video_capture.release()
    cv2.destroyAllWindows()
    return HttpResponse('Scanner closed', last_face)

unknown_face_count = 1
def save_unknown_face_screenshot(frame, top, right, bottom, left):
    global unknown_face_count
    unknown_faces_folder = os.path.join(current_path, 'D:/Capstone Project/static/unknown_faces')
    os.makedirs(unknown_faces_folder, exist_ok=True)
    # Generate a unique filename based on timestamp
    filename = f"unknown_{unknown_face_count}.png"
    filepath = os.path.join(unknown_faces_folder, filename)

    # Save the screenshot of the unknown face
    unknown_face_image = frame[top:bottom, left:right]
    cv2.imwrite(filepath, unknown_face_image)

    # Save the unknown face log in the database
    unknown_face = UnknownFace(image=filename)
    unknown_face.save()
    unknown_face_count += 1  
    print(f"Screenshot of unknown face saved: {filepath}")



def profiles(request):
    profiles = Profile.objects.all()
    context = {
        'profiles': profiles
    }
    return render(request, 'core/profiles.html', context)


def details(request):
    try:
        last_face = LastFace.objects.last()
        profile = Profile.objects.get(Q(image__icontains=last_face))
    except:
        last_face = None
        profile = None

    context = {
        'profile': profile,
        'last_face': last_face
    }
    return render(request, 'core/details.html', context)


def add_profile(request):
    form = ProfileForm()

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('profiles')

    context = {'form': form}
    return render(request, 'core/add_profile.html', context)

def edit_profile(request, id):
    profile = Profile.objects.get(id=id)
    form = ProfileForm(instance=profile)

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            # Check if a new image is provided
            if 'image' in request.FILES:
                # Delete the old image file
                old_image_path = os.path.join('D:/Capstone Project/media', str(profile.image))
                if default_storage.exists(old_image_path):
                    default_storage.delete(old_image_path)

                # Set the new image to the profile
                profile.image = request.FILES['image']

            form.save()
            return redirect('profiles')

    context = {'form': form}
    return render(request, 'core/add_profile.html', context)


def delete_profile(request, id):
    profile = Profile.objects.get(id=id)
    profile.delete()
    return redirect('profiles')


def clear_history(request):
    history = LastFace.objects.all()
    history.delete()
    return redirect('index')


def reset(request):
    profiles = Profile.objects.all()
    for profile in profiles:
        if profile.present == True:
            profile.present = False
            profile.save()
        else:
            pass
    return redirect('index')
# def unknown_faces(request):
#     unknown_faces = UnknownFace.objects.all().order_by('-timestamp')
#     context = {'unknown_faces': unknown_faces}
#     return render(request, 'core/unknown_faces.html', context)

# def delete_unknown_face(request, id):
#     unknown_face = UnknownFace.objects.get(id=id)
#     unknown_face.delete()
#     return redirect('unknown_faces')

# def clear_unknown_faces(request):
#     unknown_faces = UnknownFace.objects.all()
#     unknown_faces.delete()
#     return redirect('unknown_faces')

class UnknownFacesListView(View):
    def get(self, request):
        unknown_faces = UnknownFace.objects.all()
        return render(request, 'core/unknown_faces.html', {'unknown_faces': unknown_faces})

class DeleteUnknownFaceView(View):
    def get(self, request, face_id):
        face = get_object_or_404(UnknownFace, id=face_id)

        # Delete the image file from the backend
        image_path = os.path.join('D:/Capstone Project/static/unknown_faces', str(face.image))
        if os.path.exists(image_path):
            os.remove(image_path)

        # Delete the database record
        face.delete()

        return redirect('unknown_faces')

class ClearUnknownFacesView(View):
    def get(self, request):
        # Delete all unknown faces and their corresponding image files
        unknown_faces = UnknownFace.objects.all()
        for face in unknown_faces:
            image_path = os.path.join('D:/Capstone Project/static/unknown_faces', str(face.image))
            if os.path.exists(image_path):
                os.remove(image_path)
            face.delete()

        return redirect('unknown_faces')