import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Count, Avg, F
from django.db import models
from django.utils import timezone
from .models import Survey, Question, AnswerOption, SurveyCompletion, Answer

@login_required
def survey_list(request):
    surveys = Survey.objects.filter(author=request.user).values('id', 'title', 'created_at')
    return JsonResponse({'surveys': list(surveys)})

@login_required
@csrf_exempt
def survey_create(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        survey = Survey.objects.create(
            title=data['title'],
            author=request.user
        )
        return JsonResponse({'id': survey.id, 'title': survey.title})

@login_required
@csrf_exempt
def survey_update(request, survey_id):
    survey = Survey.objects.get(id=survey_id, author=request.user)
    if request.method == 'PUT':
        data = json.loads(request.body)
        survey.title = data.get('title', survey.title)
        survey.save()
        return JsonResponse({'id': survey.id, 'title': survey.title})

@login_required
def survey_detail(request, survey_id):
    survey = Survey.objects.get(id=survey_id)
    data = {
        'id': survey.id,
        'title': survey.title,
        'author': survey.author.username,
        'created_at': survey.created_at,
        'questions': list(survey.questions.order_by('order').values('id', 'text', 'order'))
    }
    return JsonResponse(data)

@login_required
@csrf_exempt
def question_create(request, survey_id):
    survey = Survey.objects.get(id=survey_id, author=request.user)
    data = json.loads(request.body)
    max_order = survey.questions.aggregate(models.Max('order'))['order__max'] or 0
    question = Question.objects.create(
        survey=survey,
        text=data['text'],
        order=max_order + 1
    )
    return JsonResponse({'id': question.id, 'text': question.text, 'order': question.order})

@login_required
@csrf_exempt
def question_reorder(request, survey_id):
    survey = Survey.objects.get(id=survey_id, author=request.user)
    data = json.loads(request.body)
    for item in data['questions']:
        Question.objects.filter(id=item['id'], survey=survey).update(order=item['order'])
    return JsonResponse({'status': 'ok'})

@login_required
@csrf_exempt
def option_create(request, question_id):
    question = Question.objects.get(id=question_id, survey__author=request.user)
    data = json.loads(request.body)
    max_order = question.options.aggregate(models.Max('order'))['order__max'] or 0
    option = AnswerOption.objects.create(
        question=question,
        text=data['text'],
        order=max_order + 1
    )
    return JsonResponse({'id': option.id, 'text': option.text, 'order': option.order})

@login_required
@csrf_exempt
def option_reorder(request, question_id):
    question = Question.objects.get(id=question_id, survey__author=request.user)
    data = json.loads(request.body)
    for item in data['options']:
        AnswerOption.objects.filter(id=item['id'], question=question).update(order=item['order'])
    return JsonResponse({'status': 'ok'})

@login_required
def survey_stats(request, survey_id):
    survey = Survey.objects.get(id=survey_id, author=request.user)
    completions = SurveyCompletion.objects.filter(survey=survey, completed_at__isnull=False)
    
    total_responses = completions.count()
    
    questions_stats = []
    for question in survey.questions.all():
        answers = Answer.objects.filter(question=question, completion__in=completions)
        
        if question.options.exists():
            popular = list(answers.values('selected_options__text').annotate(
                count=Count('id')
            ).order_by('-count')[:5])
        else:
            popular = list(answers.values('text_answer').annotate(
                count=Count('id')
            ).exclude(text_answer=None).exclude(text_answer='').order_by('-count')[:5])
        
        questions_stats.append({
            'question_id': question.id,
            'question_text': question.text,
            'total_answers': answers.count(),
            'popular_answers': popular
        })
    
    stats = {
        'survey_id': survey.id,
        'title': survey.title,
        'total_responses': total_responses,
        'questions_stats': questions_stats
    }
    
    if completions.exists():
        avg_time = completions.annotate(
            duration=F('completed_at') - F('started_at')
        ).aggregate(avg=Avg('duration'))['avg']
        if avg_time:
            stats['average_completion_seconds'] = avg_time.total_seconds()
    
    return JsonResponse(stats)

@login_required
def api_next_question(request, survey_id):
    survey = Survey.objects.get(id=survey_id)
    completion, created = SurveyCompletion.objects.get_or_create(
        survey=survey,
        user=request.user,
        defaults={'started_at': timezone.now()}
    )
    
    if completion.completed_at:
        return JsonResponse({'status': 'completed'})
    
    current = completion.current_question
    if not current:
        current = survey.questions.order_by('order').first()
        if current:
            completion.current_question = current
            completion.save()
    
    if not current:
        return JsonResponse({'error': 'no questions'}, status=404)
    
    questions = list(survey.questions.order_by('order'))
    current_idx = questions.index(current)
    next_q = questions[current_idx + 1] if current_idx + 1 < len(questions) else None
    
    return JsonResponse({
        'question': {
            'id': current.id,
            'text': current.text,
            'options': [{'id': o.id, 'text': o.text} for o in current.options.order_by('order')]
        },
        'next_question_id': next_q.id if next_q else None,
        'progress': {
            'current': current_idx + 1,
            'total': len(questions)
        }
    })

@login_required
@csrf_exempt
def api_save_answer(request, survey_id):
    survey = Survey.objects.get(id=survey_id)
    completion = SurveyCompletion.objects.get(survey=survey, user=request.user, completed_at__isnull=True)
    data = json.loads(request.body)
    
    question = Question.objects.get(id=data['question_id'], survey=survey)
    
    answer, created = Answer.objects.get_or_create(
        completion=completion,
        question=question
    )
    
    if question.options.exists():
        option_id = data.get('option_id')
        
        if option_id:
            try:
                option = AnswerOption.objects.get(id=option_id, question=question)
                answer.selected_options.add(option)
            except AnswerOption.DoesNotExist:
                return JsonResponse({'error': f'Option {option_id} does not exist for this question'}, status=400)
    
        else:
            if question.is_required:
                return JsonResponse({'error': 'Answer is required'}, status=400)
    
    else:
        text_answer = data.get('text_answer', '')
        if question.is_required and not text_answer:
            return JsonResponse({'error': 'Text answer is required'}, status=400)
        answer.text_answer = text_answer
    
    answer.save()
    
    questions = list(survey.questions.order_by('order'))
    current_idx = questions.index(question)
    next_q = questions[current_idx + 1] if current_idx + 1 < len(questions) else None
    
    if next_q:
        completion.current_question = next_q
        completion.save()
        return JsonResponse({'next_question_id': next_q.id})
    else:
        completion.completed_at = timezone.now()
        completion.current_question = None
        completion.save()
        return JsonResponse({'status': 'completed'})