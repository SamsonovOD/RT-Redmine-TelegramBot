from redminelib import Redmine
import telebot
import re, pprint

redmine = Redmine('http://lab.rt.ru/', username=open("username.txt", "r").read(), password=open("password.txt", "r").read()) # Авторизация RedMine API
bot = telebot.TeleBot(open("auth.txt", "r").read()) # Запуск Telegram Bot

def bot_send(user_id, text): # Отправка сообщения в чат
    bot.send_message(user_id, text)
    
def rm_get_id(s): # Полчуить ID проекта по имени
    for i in redmine.project.all():
        if(s) == i.name:
            return i.id

def print_ticket(ticket): # Вывести содержание тикета в строку
    dic = {}
    ret_str = "["
    jour = ""
    if hasattr(ticket, 'id'):
        ret_str += str(ticket.id) + ": "
        dic['id'] = str(ticket.id)
    if hasattr(ticket, 'subject'):
        ret_str += "Тема: "+str(ticket.subject)
        dic['subject'] = str(ticket.subject)
    if hasattr(ticket, 'status'):
        ret_str += "\nСтатус: "+ str(ticket.status) 
        dic['status'] = str(ticket.status)
    # if hasattr(ticket, 'priority'):
        # ret_str += "\nПриоритет: "+ str(ticket.priority)
        # dic['priority'] = str(ticket.priority)
    if hasattr(ticket, 'author'):
        ret_str += "\nАвтор: "+ str(ticket.author) 
        dic['author'] = str(ticket.author)
    if hasattr(ticket, 'assigned_to'):
        ret_str += "\nНазначен: "+ str(ticket.assigned_to) 
        dic['assigned_to'] = str(ticket.assigned_to)
    if hasattr(ticket, 'description'):
        if len(ticket.description) > 300: # Если описание тикета слишеом длинное
            ret_str += "\nОписание: "+ str(ticket.description)[0:300]+"..."
            dic['description'] = str(ticket.description)[0:300]
        else:
            ret_str += "\nОписание: "+ str(ticket.description) 
            dic['description'] = str(ticket.description)
    if hasattr(ticket, 'start_date'):
        ret_str += "\nДата: " + str(ticket.start_date) 
        dic['start_date'] = str(ticket.start_date)
    if hasattr(ticket, 'updated_on'):
        ret_str += "\nОбновлено: " + str(ticket.updated_on) 
        dic['updated_on'] = str(ticket.updated_on)
    if hasattr(ticket, 'watchers'):
        ret_str += "\nНаблюдатели:"
        for i in ticket.watchers:
            ret_str += " " + str(i.name)
        dic['watchers'] = str(ticket.watchers)
    if hasattr(ticket, 'journals'):
        # ret_str += "\nЖурналы:"
        for i in ticket.journals:
            for j in i.details:
                in_name = j['new_value']
                if str(j['name']) == "assigned_to_id":
                    try:
                        in_name = redmine.user.get(j['new_value'])
                    except:
                        in_name = j['new_value']
                jour += "\n> " + str(i.user) + " " + str(j['name']) + " " + str(in_name)
            if hasattr(i, 'notes') and len(str(i.notes)) > 1:
                jour += " : " + str(i.notes)
            dic['journals'] = i
    # if hasattr(ticket, 'relations'):
        # if len(ticket.relations) > 0:
            # ret_str += "\nСвязи:"
            # for i in ticket.relations:
                # if hasattr(i, 'id'):
                    # ret_str += " " + str(i.id)
                # if hasattr(i, 'subject'):
                    # ret_str += " "+ str(i.subject)
        # dic['relations'] = str(ticket.relations)
    ret_str += "]\n"
    return ret_str, dic, jour
    
def rm_get_projects(): # Вывести список проектов (Предположительно до 61: Sagemcom F@st 5655V2 включительно)
    return redmine.project.all(limit=47)
    
def rm_get_projtickets(p_id): #Вывести список тикетов в проекте
    return redmine.issue.filter(project_id=p_id, status_id='*')
    
def rm_get_subprojtickets(p_id, sp_id): #Вывести список тикетов в подроекте проекта
    return redmine.issue.filter(project_id=p_id, subproject_id=sp_id, status_id='*')
    
def rm_new_proj(name, p_id, desc): #Создать новый проект
    return redmine.project.create(
        name = name,
        identifier = p_id,
        description = desc,
    )

def rm_new_subproj(name, p_id, sp_id, desc): #Добавить новый подпроект в проект
    return redmine.project.create(
        name = name,
        parent_id = sp_id,
        identifier = p_id,
        description = desc,
    )
    
def rm_delete_project(p_id): # Удалить проект
    p = redmine.project.get(p_id)
    p.delete()

def rm_new_ticket(name, p_id, desc, status): #Добавить новый тикет в проект
    return redmine.issue.create(
        subject=name,
        project_id=p_id,
        description=desc,
        status_id=status,
    )
    
def rm_update_ticket(p_id, note, status): #Обновить тикет
    return redmine.issue.update(p_id, notes=note, status_id=status)
    
@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    tickets = {}
    
    getmsg = message.text.split(" ")
    
    ret = "MSG: "
    for i in getmsg:
        ret += "[" + i + "], "
    # bot_send(message.from_user.id, ret)
    
    if getmsg[0] == "/help":
        bot_send(message.from_user.id, "> Показать Проекты")
        bot_send(message.from_user.id, "> Показать Тикеты %Проект%")
        bot_send(message.from_user.id, "> Показать Тикеты %Проект% %Подпроект%")
        bot_send(message.from_user.id, "> Добавить Проект %Проект%")
        bot_send(message.from_user.id, "> Добавить Тикет %Название% В %Проект% Описание %Текст%")
        bot_send(message.from_user.id, "> Изменить Тикет %Название% В %Проект% Статус %Closed/Resolved/In Progress/Rejected% Комментарий %Текст%")
    elif getmsg[0] == "Привет":
        bot_send(message.from_user.id, "Тестовое сообщение.")
    elif getmsg[0] == "Показать":
        if len(getmsg) > 1:
            if getmsg[1] == "Проекты": # Вывести список проектов
                for i in rm_get_projects():
                    bot_send(message.from_user.id, "[" + str(i.id) + ": " + i.name + ": " + i.identifier + "]\n")
            elif getmsg[1] == "Тикеты":
                if len(getmsg) > 2:
                    if len(getmsg) > 3: # Показать тикеты подпроекта
                        get = ""
                        for i in getmsg[3:len(getmsg)-1]:
                            get += i + " "
                        get += getmsg[len(getmsg)-1]
                        bot_send(message.from_user.id, getmsg[2])
                        bot_send(message.from_user.id, get)
                        for i in rm_get_subprojtickets(rm_get_id(getmsg[2]), rm_get_id(get)):
                            out, add, jr = print_ticket(i)
                            bot_send(message.from_user.id, out)
                            bot_send(message.from_user.id, "Журнал:\n"+jr)
                            tickets[add['id']] = add
                    else: # Показать тикеты проекта
                        get = ""
                        for i in getmsg[2:len(getmsg)-1]:
                            get += i + " "
                        get += getmsg[len(getmsg)-1]
                        # bot_send(message.from_user.id, get)
                        for i in rm_get_projtickets(rm_get_id(get)):
                            out, add, jr = print_ticket(i)
                            bot_send(message.from_user.id, out)
                            bot_send(message.from_user.id, "Журнал:\n")
                            bot_send(message.from_user.id, jr)
                            tickets[add['id']] = add
                else:
                    bot_send(message.from_user.id, "Неверная команда, проверь в /help.")
            else:
                bot_send(message.from_user.id, "Неверная команда, проверь в /help.")
        else:
            bot_send(message.from_user.id, "Неверная команда, проверь в /help.")
    elif getmsg[0] == "Добавить": 
        if len(getmsg) > 1:
            if len(getmsg) > 3:
                if getmsg[1] == "Проект": # Новый подпроект в новом проекте
                    p_id = re.sub('[^0-9a-zA-Z]+', '-', getmsg[2].lower())
                    project = project = rm_new_proj(getmsg[2], p_id, 'Bot Api Test')
                    bot_send(message.from_user.id, p_id+": Добавено")
                    get = ""
                    for i in getmsg[3:len(getmsg)-1]:
                        get += i + " "
                    get += getmsg[len(getmsg)-1]
                    p_id = re.sub('[^0-9a-zA-Z]+', '-', get.lower())
                    project = rm_new_subproj(get, p_id, rm_get_id(getmsg[2]), 'Bot Api Test')
                    bot_send(message.from_user.id, p_id+": Добавено")
                elif getmsg[1] == "Тикет": # Новый тикет
                    if "В" in getmsg and "Описание" in getmsg:
                        a = getmsg.index("В")
                        b = getmsg.index("Описание")
                        
                        name = ""
                        for i in getmsg[2:a-1]:
                            name += i + " "
                        name += getmsg[a-1]
                        bot_send(message.from_user.id, name)
                        
                        proj = ""
                        for i in getmsg[a+1:b-1]:
                            proj += i + " "
                        proj += getmsg[b-1]
                        bot_send(message.from_user.id, proj)
                        
                        desc = ""
                        for i in getmsg[b+1:len(getmsg)-1]:
                            desc += i + " "
                        desc += getmsg[len(getmsg)-1]
                        bot_send(message.from_user.id, desc)
                        
                        bot_send(message.from_user.id, "Добавено")
                        issue = rm_new_ticket(name, rm_get_id(proj), desc, 1)
                    else:
                        bot_send(message.from_user.id, "Неверная команда, проверь в /help.")
                else:
                    bot_send(message.from_user.id, "Неверная команда, проверь в /help.")
            else:
                bot_send(message.from_user.id, "Неверная команда, проверь в /help.")
        else:
            bot_send(message.from_user.id, "Неверная команда, проверь в /help.")
    elif getmsg[0] == "Изменить": # Обновление тикета
        if len(getmsg) > 8:
            a = getmsg.index("Тикет")
            b = getmsg.index("В")
            c = getmsg.index("Статус")
            d = getmsg.index("Комментарий")
            
            ticket = ""
            for i in getmsg[a+1:b-1]:
                ticket += i + " "
            ticket += getmsg[b-1]
            
            project = ""
            for i in getmsg[b+1:c-1]:
                project += i + " "
            project += getmsg[c-1]
            
            status = ""
            for i in getmsg[c+1:d-1]:
                status += i + " "
            status += getmsg[d-1]
            
            if status == "Closed" or status == "Resolved" or status == "In Progress" or status == "Rejected":
                if status == "In Progress":
                    stat = 2
                elif status == "Resolved":
                    stat = 3
                elif status == "Closed":
                    stat = 5
                elif status == "Rejected":
                    stat = 6
    
                comment = ""
                for i in getmsg[d+1:len(getmsg)-1]:
                    comment += i + " "
                comment += getmsg[len(getmsg)-1]
                
                p_id = 0
                s = rm_get_projtickets(rm_get_id(project))
                for i in s:
                    if i.subject == ticket:
                        p_id = i.id
                if p_id != 0:
                    rm_update_ticket(p_id, comment, stat)
                    bot_send(message.from_user.id, "Тикет обновлён")
                else:
                    bot_send(message.from_user.id, "Тикет не найден")
            else:
                bot_send(message.from_user.id, "Статус неверный")
        else:
            bot_send(message.from_user.id, "Неверная команда, проверь в /help.")
    # elif getmsg[0] == "Удалить":
        # if len(getmsg) > 1:
            # get = ""
            # for i in getmsg[1:len(getmsg)-1]:
                # get += i + " "
            # get += getmsg[len(getmsg)-1]
            # rm_delete_project(rm_get_id(get))
            # bot_send(message.from_user.id, get+": Удалено.")
        # else:
            # bot_send(message.from_user.id, "Удалить?")
    else:
        bot_send(message.from_user.id, "Неверная команда, проверь в /help.")


# @bot.message_handler(content_types=['document'])
# def get_media_messages(message):
    # file = message.document
    # file_info = bot.get_file(file.file_id)
    # if message.caption != None:
        # getmsg = message.caption.split(" ")
        # get = ""
        # for i in getmsg[1:len(getmsg)-1]:
            # get += i + " "
        # get += getmsg[len(getmsg)-1]    
        # bot_send(message.from_user.id, "Файл: " + file.file_name + " "+ get)
        # data = bot.download_file(file_info.file_path)
        # with open(file.file_name, 'wb') as f:
            # f.write(data)
        # id = redmine.upload(file.file_name)["token"].split(".")[0]
        # f = redmine.file.get(id)
        # bot_send(message.from_user.id, "Файл id: " + str(id))

bot.polling(none_stop=True, interval=0)