# Триггер скриптов Home Assistant
# author: Timhok

import os
import random

from vacore import VACore

modname = os.path.basename(__file__)[:-3] # calculating modname

# функция на старте
def start(core:VACore):
    manifest = {
        "name": "Триггер скриптов Home Assistant",
        "version": "1.0",
        "require_online": True,

        "default_options": {
            "hassio_url": "http://hassio.lan:8123/",
            "hassio_key": "", # получить в /profile, "Долгосрочные токены доступа"
            "default_reply": [ "Хорошо", "Выполняю", "Будет сделано" ], # ответить если в описании скрипта не указан ответ в формате "ttsreply(текст)"
        },

        "commands": {
            "хочу|сделай|я буду": hassio_run_script,
        }
    }
    return manifest

def start_with_options(core:VACore, manifest:dict):
    pass
    
def exec_script(core:VACore,script,hassio_scripts):
   
    options = core.plugin_options(modname) 
    
    import requests

    url = options["hassio_url"] + "api/services/script/" + str(script)
    headers = {"Authorization": "Bearer " + options["hassio_key"]}
    res = requests.post(url, headers=headers) # выполняем скрипт
    script_desc = str(hassio_scripts[script]["description"]) # бонус: ищем что ответить пользователю из описания скрипта
    if "ttsreply(" in script_desc and ")" in script_desc.split("ttsreply(")[1]: # обходимся без re :^)
        core.play_voice_assistant_speech(script_desc.split("ttsreply(")[1].split(")")[0])
    else: # если в описании ответа нет, выбираем случайный ответ по умолчанию
        core.play_voice_assistant_speech(options["default_reply"][random.randint(0, len(options["default_reply"]) - 1)])


def hassio_run_script(core:VACore, phrase:str):

    options = core.plugin_options(modname)

    if options["hassio_url"] == "" or options["hassio_key"] == "":
        print(options)
        core.play_voice_assistant_speech("Нужен ключ или ссылка для Хоум Ассистента")
        return

    try:
        import requests
        url = options["hassio_url"] + "api/services"
        headers = {"Authorization": "Bearer " + options["hassio_key"]}
        res = requests.get(url, headers=headers) # запрашиваем все доступные сервисы
        hassio_services = res.json()
        hassio_scripts = []
        # print(hassio_services)
        for service in hassio_services: # ищем скрипты среди списка доступных сервисов
            if service["domain"] == "script":
                hassio_scripts = service["services"]
                break

        hassio_scripts_by_name = {}
        
        for script in hassio_scripts: # сформируем словарь для нечеткого поиска
            key = str(hassio_scripts[script]["name"])
            hassio_scripts_by_name[key] = script
        
        res = core.find_best_cmd_with_fuzzy(phrase,hassio_scripts_by_name,True) #сделаем вызов нечеткого поиска
        # print("res:" + res)
        if res is not None: #если нечеткий поиск вернул результат
            keyall, probability, rest_phrase = res
            script = hassio_scripts_by_name[keyall]
            exec_script(core,script,hassio_scripts)
        else: 
            core.play_voice_assistant_speech("Не могу помочь с этим")

    except:
        import traceback
        traceback.print_exc()
        core.play_voice_assistant_speech("Не получилось выполнить скрипт")
        return
