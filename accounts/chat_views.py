import json
import os
import requests
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django_ratelimit.decorators import ratelimit

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.1-8b-instant"

SYSTEM_PROMPT = """You are STAN, a warm and friendly AI assistant for Edosaic — a Student Management System.

Personality: Helpful, conversational, and professional. Use a natural, casual tone like talking to a colleague. No emojis in normal replies. Greet users warmly when they say hi.

You help visitors learn about the platform. Keep responses concise (2-4 sentences max).
Key features: role-based dashboards (admin, faculty, student, parent), attendance tracking, 
grade management, fee tracking, analytics, reports, Google/GitHub login, dark/light theme, 
AI chat assistant. Built with Django + PostgreSQL. Free for small institutions.

CRITICAL — Registration redirect: When someone asks about registering, signing up, creating an institution, getting started, or trying the platform, ALWAYS reply with this exact format:
"Great choice! You can register your institution right here:
https://edosaic.onrender.com/signup/

Just click the link, enter your invite code, and you're all set to start managing your institution!"
Never skip the URL. Always include it.

When the conversation naturally ends (user says thanks, bye, got it, or similar), add this at the very end on a new line:
[FEEDBACK]"""


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
            show_feedback = '[FEEDBACK]' in text
            text = text.replace('[FEEDBACK]', '').strip()
            return JsonResponse({'reply': text, 'show_feedback': show_feedback})
        elif 'error' in result:
            return JsonResponse({'error': f"AI error: {result['error'].get('message', 'Unknown')}"}, status=500)
        else:
            return JsonResponse({'error': 'No response from AI.'}, status=500)
    except Exception as e:
        return JsonResponse({'error': f'AI error: {str(e)}'}, status=500)
