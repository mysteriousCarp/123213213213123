from flask import Flask, request, jsonify, redirect, send_file, session
import logging
import secrets
import threading
app = Flask(__name__)
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
locked = True
app.secret_key = secrets.token_hex(16)
asks = []
allowed = False
ret2save = -1
save = [
                {
                    'name': 'Введите свою почту',
                    'answers': []
                },
{
                    'name': 'Введите ваше имя',
                    'answers': []
                }
            ]
def console_listener():
    while True:
        global locked, asks, allowed, ret2save
        command = input("Введите команду: ")
        if command == "open":
            locked = False
            asks = save

        if command == 'close':
            locked = True
            allowed = False

            asks = save
        if command == 'allow':
            allowed = True
        if command == 'd':
            allowed = False
        if allowed == False and command == 'lv':
            asks = [{
                    'name': 'короче меня угараздило в тебя каким то боком влюбиться можешь отшить и мы спокойно разойдёмся?',
                    'answers': ['да', 'нет']
                }]
            ret2save = 1

@app.route('/')
def index():
    print(f'ip: {request.remote_addr} load link')

    # Проверяем, есть ли у пользователя сессия (куки)
    if 'user_data' in session:
        # Если сессия есть - пользователь авторизован
        print(f'User {request.remote_addr} has session: {dict(session)}')

        # Проверяем locked
        if not locked:
            return send_file('main.html')
        else:
            return redirect('https://peopletalk.ru/article/test-kakoj-ty-pelmen/')

    # Если сессии нет
    else:
        print(f'User {request.remote_addr} has NO session')

        # Если allowed активна - выдаем сессию
        if allowed:
            # Создаем сессию для пользователя
            session['user_data'] = {
                'ip': request.remote_addr,
                'user_data': request.user_agent.string,
            }
            print(f'Session created for {request.remote_addr}')

            # Проверяем locked
            if not locked:
                return send_file('main.html')
            else:
                return redirect('https://peopletalk.ru/article/test-kakoj-ty-pelmen/')

        # Если allowed не активна и сессии нет - блокируем доступ
        else:
            print(f'Access denied for {request.remote_addr} - no session and allowed=False')
            return redirect('https://peopletalk.ru/article/test-kakoj-ty-pelmen/')


@app.route('/track', methods=['POST'])
def track():
    data = request.json


    for event in data.get('events', []):
        event_type = event.get('eventType')

        # СОДЕРЖАНИЕ СОБЫТИЯ
        if event_type == 'click':
            target = event.get('target', {})
            content = f"кликнул по {target.get('tagName', 'элементу')}"
            if target.get('textContent'):
                content += f" с текстом '{target.get('textContent')}'"

        elif event_type == 'keypress':
            content = f"нажал клавишу '{event.get('key', 'unknown')}'"

        elif event_type == 'scroll':
            content = f"проскроллил на {event.get('scrollPercent', 0)}%"

        elif event_type == 'session_start':
            content = "начал сессию"

        elif event_type == 'pageview':
            content = f"перешел с {event.get('previousUrl', 'начала')} на {event.get('newUrl', 'текущую')}"

        elif event_type == 'page_hide':
            content = "свернул/ушел с вкладки"

        elif event_type == 'page_show':
            content = "вернулся на вкладку"

        else:
            content = f"событие {event_type}"

        # А ПОТОМ УЖЕ СЛУЖЕБНАЯ ХУЙНЯ
        print(
            f"{content} | ip: {request.remote_addr} | url: {event.get('url', '').split('/')[-1] or '/'}")

    return jsonify({'status': 'ok'}), 200



@ app.route('/questions', methods=['GET'])
def get_questions():
    """
    Одна функция, которая читает массив asks и возвращает вопросы
    в формате, совместимом с Google Forms стилем
    """
    # Преобразуем массив asks в нужный формат
    questions = []

    for index, ask in enumerate(asks):
        question = {
            'id': index + 1,
            'text': ask.get('name', ''),
            'required': True  # Можно настроить по необходимости
        }

        # Определяем тип вопроса на основе answers
        answers = ask.get('answers', [])

        if not answers or len(answers) == 0:
            # Если нет вариантов ответа - текстовое поле
            question['type'] = 'text'
            question['placeholder'] = 'Введите ваш ответ'
        elif len(answers) <= 5:
            # Если вариантов немного - radio кнопки
            question['type'] = 'radio'
            question['options'] = answers
        else:
            # Если вариантов много - выпадающий список
            question['type'] = 'select'
            question['options'] = answers

        questions.append(question)

    # Формируем ответ в формате Google Forms
    response = {
        'title': 'Опрос Google Forms',
        'description': 'Пожалуйста, ответьте на следующие вопросы',
        'questions': questions
    }
    if questions:
        return jsonify(response)
    else:
        return redirect('https://peopletalk.ru/article/test-kakoj-ty-pelmen/')


@app.route('/submit', methods=['POST'])
def submit_answers():
    """Принимает ответы пользователя"""
    global asks,ret2save, locked
    try:
        data = request.json
        print(f"Получены ответы: {data}")
        from datetime import datetime
        print(f"Время: {datetime.now()}")

        # Здесь можно сохранить в файл или базу данных
        with open('answers.txt', 'a', encoding='utf-8') as f:
            f.write(f"\n=== {datetime.now()} ===\n")
            for key, value in data.items():
                f.write(f"{key}: {value}\n")
            f.write("-" * 50 + "\n")
        if ret2save == 1:
            ret2save = 0
            asks = save
            locked = True

        return jsonify({
            'status': 'success',
            'message': 'Ответы сохранены'
        }), 200

    except Exception as e:
        print(f"Ошибка: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
if __name__ == '__main__':
    threading.Thread(target=console_listener, daemon=True).start()
    app.run(host='0.0.0.0', port=5000)
