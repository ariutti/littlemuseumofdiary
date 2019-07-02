# README

Per far girare correttamente il codice raspberry che utilizza il convertitore MCP3008 occorre dapprima abilitare 
il modulo kernel SPI usando il menù "Preferences/Raspberry Pi Config" e indicare dal sottomenù "Interfaces" l'interfaccia SPI.

## listare i device SPI da terminale

ls -l /dev/spidev*


## Se le cose sembrano non funzionare 

### effettuare il test di loopback dell'interfaccia SPI0
link: https://www.raspberrypi.org/documentation/hardware/raspberrypi/spi/README.md

dopo aver connesso direttamente i pin MOSI e MISO del raspberry tra loro

eseguire i seguenti comandi a console

scaricare il seguente programm in C

wget https://raw.githubusercontent.com/raspberrypi/linux/rpi-3.10.y/Documentation/spi/spidev_test.c

compilarlo con il comando

gcc -o spidev_test spidev_test.c

testarlo in questo modo

./spidev_test -D /dev/spidev0.0

l'output dovrebbe essere il seguente

spi mode: 0
bits per word: 8
max speed: 500000 Hz (500 KHz)

FF FF FF FF FF FF
40 00 00 00 00 95
FF FF FF FF FF FF
FF FF FF FF FF FF
FF FF FF FF FF FF
DE AD BE EF BA AD
F0 0D
