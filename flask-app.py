from flask import Flask, request
import logging
import json
import os
import random

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

cities = {
    'москва': ['1540737/daa6e420d33102bf6947',
               '213044/7df73ae4cc715175059e'],
    'нью-йорк': ['1652229/728d5c86707054d4745f',
                 '1030494/aca7ed7acefde2606bdc'],
    'париж': ["1652229/f77136c2364eb90a3ea8",
              '3450494/aca7ed7acefde22341bdc']
}

sessionStorage = {}


@app.route('/post', methods=['POST'])
def main():
    logging.info(f'Request: {request.json!r}')
    response = {
        'session': request.json['session'],
        'version': request.json['version'],
        'response': {
            'end_session': False
        }
    }
    handle_dialog(response, request.json)
    logging.info(f'Response: {response!r}')
    return json.dumps(response)


def handle_dialog(res, req):
    user_id = req['session']['user_id']
    if req['session']['new']:
        res['response']['text'] = 'Привет! Назови свое имя!'
        sessionStorage[user_id] = {
            'first_name': None,
            'test': 0,
            'city': None
        }
        res['response']['buttons'] = [{'title': 'Помощь', 'hide': True}]
        return

    if sessionStorage[user_id]['first_name'] is None:
        first_name = get_first_name(req)
        if first_name is None:
            if 'Помощь' in req['request']['original_utterance']:
                res['response']['text'] = 'Алиса понимает только существующие и распространенные имена.'
                res['response']['buttons'] = [{'title': 'Помощь', 'hide': True}]
            else:
                res['response']['text'] = \
                    'Не расслышала имя. Повтори, пожалуйста!'
                res['response']['buttons'] = [{'title': 'Помощь', 'hide': True}]
        else:
            sessionStorage[user_id]['first_name'] = first_name
            res['response'][
                'text'] = 'Приятно познакомиться, ' \
                          + first_name.title() \
                          + '. Я - Алиса. Поиграем в Угадай город?'
            res['response']['buttons'] = [{'title': 'Да', 'hide': True}, {'title': 'Нет', 'hide': True}]
    else:
        sessionStorage[user_id]['city'] = 'москва'
        if sessionStorage[user_id]['test'] == 0:
            if 'да' in req['request']['original_utterance'].lower():
                res['response']['card'] = {}
                res['response']['card']['type'] = 'BigImage'
                res['response']['card']['title'] = 'Что это за город?'
                res['response']['card']['image_id'] = random.choice(cities[sessionStorage[user_id]['city']])
                sessionStorage[user_id]['test'] = 1
            elif 'нет' in req['request']['original_utterance'].lower():
                res['response']['text'] = 'Все говорят нет, а ты поиграй!'
                res['response']['buttons'] = [{'title': 'Да', 'hide': True}, {'title': 'Нет', 'hide': True}]
        else:
            if get_city(req).lower() == sessionStorage[user_id]['city']:
                sessionStorage[user_id]['test'] = 0
                res['response']['text'] = 'Правильно! Сыграем еще?'
                res['response']['buttons'] = [{'title': 'Да', 'hide': True}, {'title': 'Нет', 'hide': True},
                                              {'title': 'Да',
                                               "url": f"https://yandex.ru/maps/?mode=search&text={sessionStorage[user_id]['city']}",
                                               'hide': True}
                                              ]
            elif get_city(req).lower() != sessionStorage[user_id]['city']:
                res['response']['text'] = \
                    'Нет, это не этот город. Попробуй еще разок!'


def get_city(req):
    for entity in req['request']['nlu']['entities']:
        if entity['type'] == 'YANDEX.GEO':
            return entity['value'].get('city', 'none')


def get_first_name(req):
    for entity in req['request']['nlu']['entities']:
        if entity['type'] == 'YANDEX.FIO':
            return entity['value'].get('first_name', 'none')


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
