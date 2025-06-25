import machine
import network
import socket
import time

######### CONFIGURACIÓN WIFI #########
SSID = "Ghost"
PASSWORD = "Porsche 911"
SERVER_IP = "192.168.64.127"  # IP de tu computadora
SERVER_PORT = 8001

######### PINES PARA EL 74LS164 #########
SERIAL_PIN = machine.Pin(15, machine.Pin.OUT)   # DS (Datos)
CLOCK_PIN = machine.Pin(16, machine.Pin.OUT)    # SH_CP (Reloj)
RESET_PIN = machine.Pin(2, machine.Pin.OUT)     # MR (Reset)

######### PINES PARA LOS 3 LEDs (EXCESO-3) #########
excess3_pins = [
    machine.Pin(3, machine.Pin.OUT),  # O0 (LSB)
    machine.Pin(4, machine.Pin.OUT),  # O1
    machine.Pin(5, machine.Pin.OUT)   # O2
]

######### VALORES DEL DISPLAY 7 SEGMENTOS (BCD) #########
seg7_map = {
    0: 0b00111111,  # 0
    1: 0b00000110,  # 1
    2: 0b01011011,  # 2
    3: 0b01001111,  # 3
    4: 0b01100110,  # 4
    5: 0b01101101,  # 5
    6: 0b01111101,  # 6
    7: 0b00000111,  # 7
    8: 0b01111111,  # 8
    9: 0b01100111   # 9
}

######### FUNCIÓN DE CONEXIÓN WIFI #########
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)
    
    while not wlan.isconnected():
        print("Conectando a WiFi...")
        time.sleep(1)
    
    print(f"Conectado! IP: {wlan.ifconfig()[0]}")
    return wlan

######### ENVIAR DATOS AL 74LS164 #########
def send_to_shift_register(value):
    RESET_PIN.off()  # Asegúrate de que el registro no esté en modo de reset
    for i in range(8):
        SERIAL_PIN.value((value >> i) & 0x01)  # Enviar el bit menos significativo
        CLOCK_PIN.on()  # Pulsar el reloj
        CLOCK_PIN.off()  # Volver a bajar el reloj
    RESET_PIN.on()  # Opcional: activar el reset después de enviar

######### LEER VALOR EXCESO-3 #########
def read_excess3():
    return f"{excess3_pins[2].value()}{excess3_pins[1].value()}{excess3_pins[0].value()}"

######### MAIN #########
try:
    print("Iniciando...")
    connect_wifi()
    
    while True:
        try:
            # --- Leer y procesar datos ---
            digit = 5  # Ejemplo: número a mostrar en el display
            seg_value = seg7_map[digit]  # Obtener el valor de segmentos
            send_to_shift_register(seg_value)  # Enviar al registro
            
            excess3 = read_excess3()
            
            # --- Conectar al servidor y enviar ---
            sock = socket.socket()
            sock.connect((SERVER_IP, SERVER_PORT))
            data = f"7SEG:{digit};EXCESS3:{excess3}"
            sock.send(data.encode())
            print(f"Enviado: {data}")
            sock.close()
            
            time.sleep(0.5)  # Espera antes de enviar otra vez
            
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(2)
            
except KeyboardInterrupt:
    print("Programa terminado.")
