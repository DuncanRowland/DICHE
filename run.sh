rm log.dichehttp log.dichehttps
killall python
source ENV/bin/activate
nohup python ./dichehttp.py > log.dichehttp &
nohup python ./dichehttps.py > log.dichehttps &


