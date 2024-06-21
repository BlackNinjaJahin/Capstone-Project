from django.urls import path
from . import views
from .views import index, ajax, scan, profiles, details, add_profile, edit_profile, delete_profile
from .views import clear_history, reset, UnknownFacesListView, DeleteUnknownFaceView, ClearUnknownFacesView

urlpatterns = [
    path('', index, name='index'),
    path('ajax/', ajax, name='ajax'),
    path('scan/', scan, name='scan'),
    path('profiles/', profiles, name='profiles'),
    path('details/', details, name='details'),

    path('add_profile/', add_profile, name='add_profile'),
    path('edit_profile/<int:id>/', edit_profile, name='edit_profile'),
    path('delete_profile/<int:id>/', delete_profile, name='delete_profile'),

    path('clear_history/', clear_history, name='clear_history'),
    path('reset/', reset, name='reset'),

    path('unknown_faces/', UnknownFacesListView.as_view(), name='unknown_faces'),  # Update this line
    path('delete_unknown_face/<int:face_id>/', DeleteUnknownFaceView.as_view(), name='delete_unknown_face'),  # Update this line
    path('clear_unknown_faces/', ClearUnknownFacesView.as_view(), name='clear_unknown_faces'),  # Update this line
]
