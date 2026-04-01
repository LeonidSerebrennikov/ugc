Проект разворачивается на Docker, для старта: ```docker-compose up --build```. Миграции накатятся автоматически

Проект реализован как API-эндпоинты, поэтому запросы/ответы идут в формате JSON. 
Для работы с опросами нужно сначала зарегистрироваться, затем залогиниться. 

Схемы данных для отправки: 
POST /api/register/:
```
{
  "username": "string (required, min 1 char)",
  "password": "string (required, min 1 char)",
  "email": "string (optional, email format)"
}
```

POST /api/login/
```
{
  "username": "string (required)",
  "password": "string (required)"
}
```

POST /api/surveys/create/
```
{
  "title": "string (optional)"
}
```

POST /api/surveys/{survey_id}/questions/create/
```
{
  "text": "string (required)"
}
```

POST /api/surveys/{survey_id}/questions/reorder/
```
{
  "questions": [
    {
      "id": "integer (required)",
      "order": "integer (required, 0-based)"
    }
  ]
}
```

POST /api/questions/{question_id}/options/create/
```
{
  "text": "string (required, max 500 chars)"
}
```

POST /api/questions/{question_id}/options/reorder/
```
{
  "options": [
    {
      "id": "integer (required)",
      "order": "integer (required, 0-based)"
    }
  ]
}
```

POST /api/surveys/{survey_id}/save-answer/
Тут на случай, если для вопроса нет ни одного варианта ответа, предусмотрено получение ответа в виде текста
```
{
  "question_id": "integer (required)",
  "option_id": "integer (optional для варианта ответа)",
ИЛИ
  "custom_answer": "string (optional свой вариант)"
}
```
