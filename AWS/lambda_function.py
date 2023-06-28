import json
import requests
import re
from creds import *
import boto3
from boto3.dynamodb.conditions import Key

# DynamoDB =====
dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
table_whitelist = dynamodb.Table('antiSmileBot_whitelist')
table_admins = dynamodb.Table('antiSmileBot_admins')
table_autoreply = dynamodb.Table('antiSmileBot_autoreply')

# Variables =====
# Telegram api url
API_URL = 'https://api.telegram.org/bot'
# Regexp for clean text without smiles pictures
REGEX = re.compile(r'^[\w\s\!\@\#\$\%\^\&\*\(\)\+\=\"\№\;\%\:\?\{\}\[\]\:\;\'\"\«\»\<\>\,\•\⠀\ㅤ\.\/\\~\`\₽\€\-\−\–\—\¿\¡\£\¥\…\×\«\‹\»\›\„\“\‟\”\’\"\〝\〞\〟\＂\‚\‘\‛\❛\❜]*$')

# ====================================
# Functions for Telegram process =====
# Telegram API documentation: https://core.telegram.org/bots/api#message
# ====================================

# Delete message from group
def delete_message(chat_id, message_id):
    url = f'{API_URL}{API_KEY}/deleteMessage'
    payload = {
                'chat_id': chat_id,
                'message_id': message_id
                }
    try:
        r = requests.post(url,json=payload)
        return True
    except:
        return False
        
    
# Send message to chat/group
# https://core.telegram.org/bots/api#sendmessage
# Use MarkdownV2 style
def send_message(chat_id, text, message_thread_id=None):
    if message_thread_id == None:
        url = f'{API_URL}{API_KEY}/sendMessage'
        payload = {
                    'chat_id': chat_id,
                    'text': text,
                    'parse_mode': 'markdown'
                    }
    else:
        url = f'{API_URL}{API_KEY}/sendMessage'
        payload = {
                    'chat_id': chat_id,
                    'message_thread_id': message_thread_id,
                    'text': text,
                    'parse_mode': 'markdown'
                    }
    try:
        r = requests.post(url,json=payload)
        return True
    except:
        return False


# Get chat administrators
# https://core.telegram.org/bots/api#getchatadministrators
def get_chat_admins_id(chat_id):
    url = f'{API_URL}{API_KEY}/getChatAdministrators'
    payload = {
                'chat_id': chat_id
                }
    admins = []
    try:
        r = requests.post(url,json=payload)
        body = r.json()
        for adm in body['result']:
            admins.append(adm['user']['id'])
        return admins 
    except:
        return admins
        
        
# Get group chat title by id
def get_chat_title_by_id(chat_id):
    url = f'{API_URL}{API_KEY}/getChat'
    payload = {
                'chat_id': chat_id
                }
    title = str(chat_id)
    try:
        r = requests.post(url,json=payload)
        body = r.json()
        title = body['result']['title']
        return title 
    except:
        return title


# Get username by id
def get_username_by_id(chat_id):
    url = f'{API_URL}{API_KEY}/getChat'
    payload = {
                'chat_id': chat_id
                }
    title = f"User ID {str(chat_id)}"
    try:
        r = requests.post(url,json=payload)
        body = r.json()
        title = f"{body['result']['first_name']} {body['result']['last_name']} @{body['result']['username']}"
        return title 
    except:
        return title


# ====================================
# Functions for AWS DynamoDB =====
# Telegram API documentation: https://core.telegram.org/bots/api#message
# ====================================

# Get users whitelist for chat    
def get_whitelist(chat_id):
    chat_id_str = str(chat_id)
    users_list = []
    try:
        response = table_whitelist.query(
            KeyConditionExpression=Key('chat_id').eq(chat_id_str)
        )
        for user in response['Items']:
            users_list.append(user['from_id'])
        return users_list
    except:
        return users_list

        
# Get chats for admin  
def get_chats_for_admin(admin_id):
    admin_id_str = str(admin_id)
    chats_list = []
    try:
        response = table_admins.query(
            KeyConditionExpression=Key('admin_id').eq(admin_id_str)
        )
        for chat in response['Items']:
            chats_list.append(chat['chat_id'])
        return chats_list
    except:
        return chats_list
        
        
# Get autoreply for chat    
def get_autoreply(chat_id):
    chat_id_str = str(chat_id)
    text = ""
    try:
        response = table_autoreply.query(
            KeyConditionExpression=Key('chat_id').eq(chat_id_str)
        )
        for autoreply in response['Items']:
            text = str(autoreply['text'])
        return text
    except:
        return text


# Add user to whitelist
def add_to_whitelist(chat_id, sender_from):
    chat_id_str = str(chat_id)
    sender_from_str = str(sender_from)
    response = table_whitelist.put_item(
        Item = {
         "chat_id": chat_id_str,
         "from_id": sender_from_str
        }
    )
    return True
    

# Remove user from whitelist
# chat_id partition key and from_id sort key. In this case we write in json both keys
# https://beabetterdev.com/2022/04/22/how-to-delete-an-item-in-a-dynamodb-table-with-boto3/
def rem_from_whitelist(chat_id, sender_from):
    chat_id_str = str(chat_id)
    sender_from_str = str(sender_from)
    response = table_whitelist.delete_item(
        Key = {
         "chat_id": chat_id_str,
         "from_id": sender_from_str
        }
    )
    if response['ResponseMetadata']['HTTPStatusCode'] == 200:
        return True
    else:
        return False

    
# Set autoreply message for chat
def set_autoreply_for_chat(chat_id, text):
    chat_id_str = str(chat_id)
    text_str = str(text)
    response = table_autoreply.put_item(
        Item = {
         "chat_id": chat_id_str,
         "text": text_str
        }
    )
    return True
  
  
# Update autoreply message for chat
# Use UpdateExpression
# https://catalog.us-east-1.prod.workshops.aws/workshops/3d705026-9edc-40e8-b353-bdabb116c89c/en-US/persisting-data/dynamodb/step-3
def update_autoreply_for_chat(chat_id, text):
    chat_id_str = str(chat_id)
    text_str = str(text)
    response = table_autoreply.update_item(
        Key = {
            'chat_id': chat_id_str
        },
        UpdateExpression="set #text=:r",
        ExpressionAttributeNames={
            '#text': 'text'
        },
        ExpressionAttributeValues={
            ':r': text_str
        },
        ReturnValues="UPDATED_NEW"
    )
    if response['ResponseMetadata']['HTTPStatusCode'] == 200:
        return True
    else:
        return False

  
# Add user to chat admins table
def add_to_chat_admins(chat_id, admin_id):
    chat_id_str = str(chat_id)
    admin_id_str = str(admin_id)
    response = table_admins.put_item(
        Item = {
         "chat_id": chat_id_str,
         "admin_id": admin_id_str
        }
    )
    return True
    
        
# ====================================
# Main function =====
def lambda_handler(event, context):
    # Get http request from telegram
    body = json.loads(event['body'])

    try:
        msg = body['message']
        handle_message(msg)
    except:
        response = {
            'statusCode': 200
        }

    response = {
        'statusCode': 200
    }
    return response


# Processing message
def handle_message(msg):
    
    # Is video message?
    is_video = None
    try:
        is_video = msg['video']
    except:
        is_video = None
        
    # Is message in topic group?
    is_topic_message = None
    message_thread_id = None
    try:
        # Check if it group with topics
        is_forum = msg['chat']['is_forum']
        message_thread_id = msg['message_thread_id']
    except:
        is_topic_message = None
        message_thread_id = None
    
    
    # Is photo?
    is_photo = None
    try:
        # Check if it photo
        is_photo = msg['photo']
    except:
        is_photo = None

    # Is photo with caption?
    caption = None
    try:
        caption = msg['caption']
    except:
        caption = None
        
    
    # Message ID, integer
    message_id = msg['message_id']
    # Chat ID, integer or string
    chat_id = msg['chat']['id']
    # User object
    sender_from = msg['from']['id']
    
    sender_first_name = ""
    try:
        sender_first_name = msg['from']['first_name']
    except:
        sender_first_name = ""
    
    sender_last_name = ""
    try:
        sender_last_name = msg['from']['last_name']
    except:
        sender_last_name = ""
    
    sender_username = "None"
    try:
        sender_username = msg['from']['username']
        sender_username_markdown = sender_username.replace("_","\_")
    except:
        sender_username = f" {sender_first_name} {sender_last_name} id{msg['from']['id']}"
        sender_username_markdown = f" {sender_first_name} {sender_last_name} id{msg['from']['id']}"


    # Get whitelist for chat
    whitelist = get_whitelist(chat_id)


    message_text = None
    try:
        # Get text message
        message_text = msg['text']
    except:
        if is_photo == None and is_video == None:
            # Check if user not in whitelist 
            if str(sender_from) not in whitelist:
    
                # Delete message if it file, sticker, audio, etc...
                delete_message(chat_id, message_id)
                autoreply_text = get_autoreply(chat_id)
                if autoreply_text == "":
                    autoreply_text = f"Message from @{sender_username_markdown} was deleted"
                else:
                    autoreply_text = autoreply_text.replace("<sender-username>", f"@{sender_username_markdown}")
                    autoreply_text = autoreply_text.replace("<sender-id>", f"{str(sender_from)}")
                send_message(chat_id, autoreply_text, message_thread_id)
                
                response = {
                    'statusCode': 200
                }
                return response
                
        elif caption != None:
            # Check if user not in whitelist 
            if str(sender_from) not in whitelist:
                
                # Delete message if it not good for regexp
                if not REGEX.match(caption):
                    delete_message(chat_id, message_id)
                    autoreply_text = get_autoreply(chat_id)
                    if autoreply_text == "":
                        autoreply_text = f"Message from @{sender_username_markdown} was deleted"
                    else:
                        autoreply_text = autoreply_text.replace("<sender-username>", f"@{sender_username_markdown}")
                        autoreply_text = autoreply_text.replace("<sender-id>", f"{str(sender_from)}")
                    send_message(chat_id, autoreply_text, message_thread_id)
                    
                    response = {
                        'statusCode': 200
                    }
                    return response
                    
                    
    # If it text message
    
    
    # If it command
    # Add all commands in commands_list list
    commands_list = ["/start", "/getstatus", "/getmyid", "/getmygroups", "/wl", "/rem", "/add", "/ar", "/setar", "/setautoreply"]
    # Check if string starts with any string from the list
    if list(filter(message_text.startswith, commands_list)) != [] and chat_id == sender_from:

        command_param = message_text.split("_")
        
        # Bot start
        if command_param[0] == "/start":
            send_message(sender_from, f"Send me a smiley face or sticker and I'll delete it.")
            send_message(sender_from, f"For group chats, you'll be able to set up a whitelist with those who can send emoticons to the group and set up autoreply for messages with smiley face.\nTo do this:\n1) Add me to the group chat as an administrator, only with the right to delete posts\n2) Run the command /initantismilebot in group chat\n3) If you've done everything right, I'll verify that you really are a chat administrator and send you a list of control commands.")
            
        # Bot status
        if command_param[0] == "/getstatus":
            send_message(sender_from, f"Hi @{sender_username_markdown}, everything is fine!")
        
        # Get user id
        elif command_param[0] == "/getmyid":
            send_message(sender_from, f"@{sender_username_markdown}, your Telegram id: {sender_from}")
            
        # Manage group chats settings
        elif command_param[0] == "/getmygroups":
            chats = get_chats_for_admin(sender_from)
            if len(chats) > 0:
                return_text_message = "Select a group chat command for manage:\n"
                for chat in chats:
                    stripped_chat_id = chat.strip('-')
                    return_text_message += f"\n*{get_chat_title_by_id(chat)}*\nshow whitelist: /wl\_{stripped_chat_id}\nshow autoreply: /ar\_{stripped_chat_id}\nset autoreply: /setar\_{stripped_chat_id}\n"
            else:
                return_text_message = f"You do not have group chats to manage. {chats}"
            send_message(sender_from, return_text_message)
        
        # Get chat whitelist
        elif command_param[0] == "/wl":
            # In this command we strip - before. Add - for group chat here
            chat_id_str = f"-{command_param[1]}"
            # Ask telegram if user group admin
            admins = get_chat_admins_id(chat_id_str)
            text_whitelist = f"*Whitelist for {get_chat_title_by_id(chat_id_str)}*\n"
            if sender_from in admins:
                white_list = get_whitelist(chat_id_str)
                if len(white_list) > 0:
                    for wl in white_list:
                        text_whitelist += f"\nid{wl} \u2013 {get_username_by_id(wl)}\n/rem\_{wl}\_{command_param[1]}\n"
                    text_whitelist += f"\nIf you need *remove* user from whitelist, click the command /rem\_user-id\_{command_param[1]} in the list above."
                else:
                    text_whitelist += "\nWhitelist is empty.\n"
                text_whitelist += f"\nIf you want *add* user to whitelist for this group, send me command \n/add\_user-id\_{command_param[1]}"
                send_message(sender_from, text_whitelist)
                send_message(sender_from, "The user can find out his ID by sending @AntiSmileBot the /getmyid command.\nAsk the user to forward the message with user ID to you.")
            else:
                send_message(sender_from, f"Access denied!")

        # Remove user from whitelist
        elif command_param[0] == "/rem":
            user_id_str = command_param[1]
            chat_id_str = f"-{command_param[2]}"
            # Ask telegram if user group admin
            admins = get_chat_admins_id(chat_id_str)
            if sender_from in admins:
                white_list = get_whitelist(chat_id_str)
                if len(white_list) > 0:
                    if user_id_str in white_list:
                        response = rem_from_whitelist(chat_id_str, user_id_str)
                        if response == True:
                            text = f"I remove user *{get_username_by_id(user_id_str)}* from whitelist for *{get_chat_title_by_id(chat_id_str)}*.\nShow whitelist for this group: /wl\_{command_param[2]}"
                        else:
                            text = f"An error occurred during deletion. Check that the user has actually been removed from the whitelist.\nShow whitelist for this group: /wl\_{command_param[2]}"
                    else:
                        text = f"User *{get_username_by_id(user_id_str)}* is not found in the whitelist."
                else:
                    text = "Whitelist is empty."
                send_message(sender_from, text)
            else:
                send_message(sender_from, f"Access denied!")
                
        # Add user to whitelist
        elif command_param[0] == "/add":
            user_id_str = command_param[1]
            chat_id_str = f"-{command_param[2]}"
            # Ask telegram if user group admin
            admins = get_chat_admins_id(chat_id_str)
            if sender_from in admins:
                white_list = get_whitelist(chat_id_str)
                if user_id_str in white_list:
                    text = f"The user *{get_username_by_id(user_id_str)}* was already in whitelist for *{get_chat_title_by_id(chat_id_str)}*.\nShow whitelist for this group: /wl\_{command_param[2]}"
                    send_message(sender_from, text)
                else:
                    text = f"I add user *{get_username_by_id(user_id_str)}* to whitelist for *{get_chat_title_by_id(chat_id_str)}*.\nShow whitelist for this group: /wl\_{command_param[2]}"
                    add_to_whitelist(chat_id_str, command_param[1])
                    send_message(sender_from, text)
            else:
                send_message(sender_from, f"Access denied!")
                
        # Get autoreply for group
        elif command_param[0] == "/ar":
            # In this command we strip - before. Add - for group chat here
            chat_id_str = f"-{command_param[1]}"
            # Ask telegram if user group admin
            admins = get_chat_admins_id(chat_id_str)
            if sender_from in admins:
                autoreply_text = get_autoreply(chat_id_str)
                if autoreply_text != "":
                    send_message(sender_from, f"Autoreply for *{get_chat_title_by_id(chat_id_str)}*:\n")
                    send_message(sender_from, autoreply_text)
                else:
                    send_message(sender_from, "Autoreply text is empty.")
            else:
                send_message(sender_from, f"Access denied!")                
                
        # Set autoreply for group. Info part
        elif command_param[0] == "/setar":
            # In this command we strip - before. Add - for group chat here
            chat_id_str = f"-{command_param[1]}"
            # Ask telegram if user group admin
            admins = get_chat_admins_id(chat_id_str)
            if sender_from in admins:
                send_message(sender_from, f"You can use tags in autoreply message:\n<sender-username> for print sender username\n<sender-id> for print user telegram ID\nAnd also you can use in your autoreply [MarkdownV2 style](https://core.telegram.org/bots/api#markdownv2-style)")
                send_message(sender_from, f"For set autoreply message for *{get_chat_title_by_id(chat_id_str)}* use command\n/setautoreply\_{command_param[1]} on first line and autoreply text on next lines. All of this should be in one message.")
                send_message(sender_from, "Example:")
                send_message(sender_from, f"/setautoreply\_{command_param[1]}\nMessage from <sender-username> was deleted.")
                send_message(sender_from, "The message above will set the autoreply message like this:")
                send_message(sender_from, "Message from @bgelov was deleted.")
            else:
                send_message(sender_from, f"Access denied!")   
                
        # Update autoreply for group. Setup part
        elif command_param[0] == "/setautoreply":
            # Split multiple line
            split_autoreply_command = command_param[1].split("\n",1)
            # In this command we strip - before. Add - for group chat here
            chat_id_str = f"-{split_autoreply_command[0]}"
            # Ask telegram if user group admin
            admins = get_chat_admins_id(chat_id_str)
            if sender_from in admins:
                autoreply_text = split_autoreply_command[1]
                if autoreply_text != "":
                    response = update_autoreply_for_chat(chat_id_str, autoreply_text)
                    if response == True:
                        send_message(sender_from, "A message has been successfully set up:")
                        new_autoreply = get_autoreply(chat_id_str)
                        send_message(sender_from, new_autoreply)
                    else:
                        text = f"An error occurred during set autoreply text. Check that the autoreply has actually been updated.\nShow autoreply for this group: /ar\_{command_param[1]}"
                else:
                    send_message(sender_from, "Autoreply text is empty.")
            else:
                send_message(sender_from, f"Access denied!")   
                
        return True
    
    
    else:
        # Init bot. Only from group chat
        if message_text == "/initantismilebot":
            if chat_id == sender_from:
                send_message(sender_from, "Use this command in group chat")
                return True
            else:
                admins = get_chat_admins_id(chat_id)
                if sender_from in admins:
                    delete_message(chat_id, message_id)
                    add_to_chat_admins(chat_id, sender_from)
                    set_autoreply_for_chat(chat_id, "Message from <sender-username> was deleted")
                    init_message = f"Hi, @{sender_username_markdown}!\nI linked your account with {get_chat_title_by_id(chat_id)}. Now you can send me the following commands:\n/getstatus - Get the bot's working status.\n/getmyid - Get your Telegram ID. To add a user.\n/getmygroups - Show your groups and manage whitelist.\n"
                    send_message(sender_from, init_message)
                    return True


    # Processing message if it not command

    # Check if user not in whitelist 
    if str(sender_from) not in whitelist:
    
        # Delete message if it not good for regexp
        if not REGEX.match(message_text):
            delete_message(chat_id, message_id)
            autoreply_text = get_autoreply(chat_id)
            if autoreply_text == "":
                autoreply_text = f"Message from @{sender_username_markdown} was deleted"
            else:
                autoreply_text = autoreply_text.replace("<sender-username>", f"@{sender_username_markdown}")
                autoreply_text = autoreply_text.replace("<sender-id>", f"{str(sender_from)}")
            send_message(chat_id, autoreply_text, message_thread_id)
    
    return True
