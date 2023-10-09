docker stop sonia_ai_project
docker rm sonia_ai_project
docker run -it -d --restart=always --name=sonia_ai_project -v .:/opt/app $(docker build -q .)