docker stop sonia_ai_project
docker rm sonia_ai_project
docker run -it -d -v $(pwd):/opt/app --restart=always --name=sonia_ai_project $(docker build -q .)