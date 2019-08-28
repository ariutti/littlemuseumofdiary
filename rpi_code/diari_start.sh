. ./config.conf
echo $DIARIO;
#cd code_mod_nicola; sudo python3 main.py upload/$DIARIO 192.168.2.100 4001 2> error.log;
cd code_mod_nicola; sudo python3 main.py /home/pi/code/upload/$DIARIO 192.168.2.100 4001;
