# Telegram-AntiSmileBot
https://t.me/AntiSmileBot

Telegram Python webhook bot on AWS infrastructure (Lambda, API Gateway, DynamoDB).

AntiSmileBot deletes posts with emoticons, stickers, and files in your telegram group chats. For group chats, you'll be able to set up a whitelist with those who can send emoticons to the group and set up autoreply for messages with a smiley face.


## How it works:
0) send /start command to @AntiSmileBot.
1) add bot to the group as administrator with delete messages permission.
2) send command /initantismilebot to the group.
3) bot send you message with admin command.


![image](https://user-images.githubusercontent.com/5302940/218295987-2b2252bb-338f-4177-bcc0-61517bce1e8b.png)


### Whitelist
You can create, view and edit whitelist for you group throught bot commands.


![image](https://user-images.githubusercontent.com/5302940/218296181-d4d1e76e-b37b-477c-97d4-f61707ae00e1.png)


### Autoreply
And you can view and set autoreply for deleted messages (with smiles).


![image](https://user-images.githubusercontent.com/5302940/218296244-3568395e-01f8-42e1-8716-adc0813d0ff3.png)


You can use tags in autoreply message:
<sender-username> for print sender username
<sender-id> for print user telegram ID
And also you can use in your autoreply MarkdownV2 style (https://core.telegram.org/bots/api#markdownv2-style)

  


