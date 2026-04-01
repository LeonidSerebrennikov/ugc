from django.urls import path
from . import views

urlpatterns = [
    path('api/surveys/', views.survey_list, name='survey_list'),
    path('api/surveys/create/', views.survey_create, name='survey_create'),
    path('api/surveys/<int:survey_id>/', views.survey_detail, name='survey_detail'),
    path('api/surveys/<int:survey_id>/update/', views.survey_update, name='survey_update'),
    path('api/surveys/<int:survey_id>/questions/create/', views.question_create, name='question_create'),
    path('api/surveys/<int:survey_id>/questions/reorder/', views.question_reorder, name='question_reorder'),
    path('api/questions/<int:question_id>/options/create/', views.option_create, name='option_create'),
    path('api/questions/<int:question_id>/options/reorder/', views.option_reorder, name='option_reorder'),
    path('api/surveys/<int:survey_id>/stats/', views.survey_stats, name='survey_stats'),
    path('api/surveys/<int:survey_id>/next-question/', views.api_next_question, name='api_next_question'),
    path('api/surveys/<int:survey_id>/save-answer/', views.api_save_answer, name='api_save_answer'),
]
