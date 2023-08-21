docker stop ai_chat_bot2
docker rm ai_chat_bot2
docker run -it -d --restart=always --name=ai_chat_bot2 $(docker build -q .)