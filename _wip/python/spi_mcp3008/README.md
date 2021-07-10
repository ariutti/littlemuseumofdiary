# README

Per far girare correttamente il codice raspberry che utilizza il convertitore MCP3008 occorre dapprima abilitare il modulo kernel SPI usando il menù "Preferences/Raspberry Pi Config" e indicare dal sottomenù "Interfaces" l'interfaccia SPI.

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

## Osservazioni

Noto che il sensore ha dei periodici momenti di detecting erroneo che si manifesta con una percezione di distanza più ravicinata di quanto sia in realtà.
Questo accade per un brevissimo istante. Tale errore sulla distanza reale è tanto maggiore quanto maggiore è la distanza cui si trova il sensore rispetto all'ostacolo.

Giusto per dare una idea:

* quando il sensore è a distanza di 7 cm dall'ostacolo, l'errore è inferiore al centimetro;
* quando il sensore invece si trova a circa 45 centimetri dall'ostacolo, l'errore aumenta fino a 6cm se non più;

Da notare che il valore del coefficiente del filtro agisce facendo da passabasso ai valori letti ma questo valore va di pari passo con la frequenza con cui le letture vengono effettuate.
Il filtro passabasso si comporta diversamente a seconda che le letture vengano fatte con maggiore o minore frequenza.
Per cui occorre fare un fine tuning anche del tempo di attesa tra un loop ed un altro.
