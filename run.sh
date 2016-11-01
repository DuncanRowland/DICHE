rm dichehttp.log dichehttps.log
killall python
source ENV/bin/activate
nohup python ./dichehttp.py > log.dichehttp &
nohup python ./dichehttps.py > log.dichehttps &


