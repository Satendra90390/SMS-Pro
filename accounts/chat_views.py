import json
import os
import requests
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django_ratelimit.decorators import ratelimit

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.1-8b-instant"

SYSTEM_PROMPT = """You are STAN, the friendly AI assistant for Edosaic - a Student Management System. 
You help visitors learn about the platform. Keep responses concise (2-4 sentences max).
Key features: role-based dashboards (admin, faculty, student, parent), attendance tracking, 
grade management, fee tracking, analytics, reports, Google/GitHub login, dark/light theme, 
AI chat assistant. Built with Django + SQLite. Free and open source.
Only answer questions about Edosaic. Politely redirect unrelated questions."""


@csrf_exempt
@require_POST
@ratelimit(key='ip', rate='10/m', method='POST', block=True)
def public_chat_api(request):
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    if not user_message:
        return JsonResponse({'error': 'Message is required'}, status=400)

    api_key = os.getenv('GROQ_API_KEY', '')
    if not api_key:
        return JsonResponse({'error': 'AI is not configured.'}, status=500)

    history = data.get('history', [])
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    for msg in history:
        role = 'user' if msg.get('role') == 'user' else 'assistant'
        parts = msg.get('parts', [])
        text = parts[0].get('text', '') if parts else ''
        messages.append({"role": role, "content": text})

    messages.append({"role": "user", "content": user_message})

    try:
        resp = requests.post(
            GROQ_URL,
            json={"model": GROQ_MODEL, "messages": messages, "temperature": 0.7, "max_tokens": 256},
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            timeout=30,
        )
        result = resp.json()

        if 'choices' in result and result['choices']:
            text = result['choices'][0]['message']['content']
            return JsonResponse({'reply': text})
        elif 'error' in result:
            return JsonResponse({'error': f"AI error: {result['error'].get('message', 'Unknown')}"}, status=500)
        else:
            return JsonResponse({'error': 'No response from AI.'}, status=500)
    except Exception as e:
        return JsonResponse({'error': f'AI error: {str(e)}'}, status=500)
