docker stop sonia_ai_project
docker rm sonia_ai_project
docker run -it -d -v $(pwd):/opt/app --restart=always -p 8080:80 --name=sonia_ai_project $(docker build -q .)