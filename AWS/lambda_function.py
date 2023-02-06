import json
import requests
import re
from creds import *
import boto3

#Connect to DB
dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
table = dynamodb.Table('antiSmileBotDB_whitelist')

#Telegram API documentation: https://core.telegram.org/bots/api#message
        
#Delete message from group
def deleteMessage(chat_id,message_id):
    url = f'{API_URL}{API_KEY}/deleteMessage'
    payload = {
                'chat_id': chat_id,
                'message_id': message_id
                }
    r = requests.post(url,json=payload)
    return True
    
#Send message to chat/group
def send_message(chat_id,textMessage):
    url = f'{API_URL}{API_KEY}/sendMessage'
    payload = {
                'chat_id': chat_id,
                'text': textMessage
                }
    r = requests.post(url,json=payload)
    return True
    

#Get users whitelist for chat    
def get_whitelist(chat_id):
    users_list = []
    try:
        response = table.get_item(Key={"chat_id": str(chat_id)})
        users_list = list(map(int,response['Item']['from_id']))
        return users_list
    except KeyError:
        return users_list
        

#Mail function
def lambda_handler(event, context):
    print(event)

    try:
        body = json.loads(event['body'])
        
        #integer
        message_id = body['message']['message_id'] 
        #Integer or String
        chat_id = body['message']['chat']['id']
        #user object
        sender_from = body['message']['from']['id']
        sender_first_name = body['message']['from']['first_name']
        sender_last_name = body['message']['from']['last_name']
        
        
        message_text = None
        try:
            message_text = body['message']['text']
        except:
            deleteMessage(chat_id,message_id)
            textMessage = f"В сообщении {str(message_id)} от пользователя {sender_first_name} {sender_last_name} с id {str(sender_from)} стикер" 
            send_message(chat_id,textMessage)
            return  {
                "statusCode": 200
            }


        whiteList = get_whitelist(chat_id)

        if int(sender_from) in whiteList:
            textMessage = f"Пользователь с id {str(sender_from)} находится в white листе"
            send_message(chat_id,textMessage)
            
        else:

            regex = re.compile(r'^[\w\s\!\@\#\$\%\^\&\*\(\)\+\=\"\№\;\%\:\?\{\}\[\]\:\;\'\"\<\>\,\.\/\\~\`\₽\€\-\−\–\—\¿\¡\£\¥]*$')

    
            if not regex.match(message_text):
                
                deleteMessage(chat_id,message_id)
                
                textMessage = f"В сообщении {str(message_id)} от пользователя {sender_first_name} {sender_last_name} с id {str(sender_from)} смайлики или запрещённые символы" 
                send_message(chat_id,textMessage)
    
                return  {
                    "statusCode": 200
                }
    except:
        return  {
        "statusCode": 200
    }