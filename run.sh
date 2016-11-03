rm logs/access.log
rm logs/http.log
rm logs/https.log
killall python
source ENV/bin/activate
nohup python ./dichehttp.py > logs/http.log &
nohup python ./dichehttps.py > logs/https.log &

