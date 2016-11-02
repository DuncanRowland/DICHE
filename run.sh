rm log.diche log.dichehttp log.dichehttps
killall python
source ENV/bin/activate
echo "<PRE>" > static/log.html
nohup python ./dichehttp.py > log.dichehttp &
nohup python ./dichehttps.py > log.dichehttps &


