from django.urls import path
from .views import RecommendationView_2

urlpatterns = [
    path('recommendation_2/', RecommendationView_2.as_view(), name='recommendation_2'),
]