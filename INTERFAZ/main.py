from PyQt5.QtWidgets import QMainWindow, QApplication
from PyQt5.uic import loadUi
from PyQt5.QtSerialPort import QSerialPort, QSerialPortInfo
from PyQt5.QtCore import QIODevice, QPoint
from PyQt5 import QtCore, QtWidgets
import numpy as np
import sys
import serial
import time
from PIL import Image
import requests
from io import BytesIO
import cv2
import numpy as np
import mysql.connector
from mysql.connector import Error

class MyApp(QMainWindow):
    def __init__(self):
        super(MyApp, self).__init__()
        loadUi('Interfaz.ui', self)

        self.bt_normal.hide()
        self.click_posicion = QPoint()
        self.bt_minimize.clicked.connect(lambda: self.showMinimized())
        self.bt_normal.clicked.connect(self.control_bt_normal)
        self.bt_maximize.clicked.connect(self.control_bt_maximize)
        self.bt_close.clicked.connect(lambda: self.close())
    
        self.setWindowFlag(QtCore.Qt.FramelessWindowHint)
        self.setWindowOpacity(1)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
    
        self.gripSize = 10
        self.grip = QtWidgets.QSizeGrip(self)
        self.grip.resize(self.gripSize, self.gripSize)

        self.frame_superior.mouseMoveEvent = self.mover_ventana

        self.serial = QSerialPort()
        self.bt_update.clicked.connect(self.read_ports)
        self.bt_connect.clicked.connect(self.serial_connect)
        self.bt_disconnect.clicked.connect(lambda: self.serial.close())
        self.read_ports()

        self.save_photo.clicked.connect(self.guardar_foto)
        self.calculate.clicked.connect(self.enviar_datos)
        self.procesing.clicked.connect(self.showImage)
        self.base_datos.clicked.connect(self.upload)
        self.mostrar_foto.clicked.connect(self.get_image)

    def read_ports(self):
        self.baudrates = ['1200', '2400', '4800', '9600', '19200', '38400', '115200']
        portList = []
        ports = QSerialPortInfo().availablePorts()
        for i in ports:
            portList.append(i.portName())

        self.cb_list_ports.clear()
        self.cb_list_baudrates.clear()
        self.cb_list_ports.addItems(portList)
        self.cb_list_baudrates.addItems(self.baudrates)
        self.cb_list_baudrates.setCurrentText('9600')

    def serial_connect(self):
        self.serial.waitForBytesWritten(100)
        self.port = self.cb_list_ports.currentText()
        self.baud = self.cb_list_baudrates.currentText()
        self.serial.setBaudRate(int(self.baud))
        self.serial.setPortName(self.port)
        self.serial.open(QIODevice.ReadWrite)

    def read_data(self):
        if not self.serial.canReadLine(): return
        rx = self.serial.readLine().decode('utf-8')
        if rx.endswith("."):
            rx = rx[:-1]
            return rx

    def send_data(self,data):
        data = data + '\n'
        print('data')
        if self.serial.isOpen():
            self.serial.write(data.encode())
    
    def guardar_foto(self):
        url = "http://192.168.9.186/cam-lo.jpg"
        response = requests.get(url)
        img = Image.open(BytesIO(response.content))

        try:
            img.save('Camara.jpg')
        except IOError:
            print("cannot convert")  #infile
            
    def obtener_lista(self):
        archivo=open("arrays.txt","r")
        contenido=archivo.read()
        lista=contenido.split("\n")
        archivo.close()
        
        general=[]
        lista1=[]
        for i in range(int((len(lista)-1)/11)):
            for j in range((11*i)+2,(11*i)+4):
                lista1.append(float(lista[j]))
                
            for k in range((11*i)+8, (11*i)+10):
                lista1.append(float(lista[k]))
            general.append(lista1)
            lista1=[]
        
        return general 
    
    def obtener_angulos(self, Lista, ancho=800, largo=800):
        
        for k in range(0,15):
            
            for j in range(0,15):
            
                for i in range(0,len(Lista)): 
            
                    if (ancho*j/15<=Lista[i][2]<ancho*(j+1)/15) and (largo*k/15<=Lista[i][3]<largo*(k+1)/15):
                        Lista[i].append(6*(j+1)) #horizontal      
                        Lista[i].append(2*(k+1)) #vertical    
        return Lista

    def calcularDistancia(self, lista_angulos):
        lista_distancia=[]
        arduino = serial.Serial('COM3',9600)
        for x in range(len(lista_angulos)):
            time.sleep(2)
            arduino.write(lista_angulos[x].encode())
            time.sleep(3)
            distancia = arduino.readline()
            number = distancia.decode().split()
            lista_distancia.append(int(number[0]))
        arduino.close()
        return lista_distancia

    def enviar_datos(self):
        listax=self.obtener_lista()
        listay=self.obtener_angulos(listax)
        listaz=[]
        print (listay)
        for i in range(len(listay)):
            angle2=str(listay[i][len(listay[i])-1])
            angle1=str(listay[i][len(listay[i])-2])
            formato = angle1 + ',' + angle2 + '/'
            listaz.append(formato)   
            print(formato)         
        
        lista_a = self.calcularDistancia(listaz)

        for y in range(len(listay)):
            listay[y].append(lista_a[y])

        #escribiendo en el archivo
        archivo=open("base_datos.txt","w")
        for i in range(len(listay)):
            archivo.write("["+"\n")
            for j in range(0,7):
                archivo.write(str(listay[i][j])+"\n")
            archivo.write("]"+"\n")
        archivo.close  

    def showImage(self):
# ----------- READ DNN MODEL -----------
# Model architecture
        prototxt = "model/MobileNetSSD_deploy.prototxt.txt"
        # Weights
        model = "model/MobileNetSSD_deploy.caffemodel"
        # Class labels
        classes = {0:"background", 1:"aeroplane", 2:"bicycle",
                3:"bird", 4:"boat",
                5:"bottle", 6:"bus",
                7:"car", 8:"cat",
                9:"chair", 10:"cow",
                11:"diningtable", 12:"dog",
                13:"horse", 14:"motorbike",
                15:"person", 16:"pottedplant",
                17:"sheep", 18:"sofa",
                19:"train", 20:"tvmonitor"}

        # Load the model
        net = cv2.dnn.readNetFromCaffe(prototxt, model)

        # ----------- READ THE IMAGE AND PREPROCESSING -----------
        image = cv2.imread("Camara.jpg")
        height, width, _ = image.shape
        image_resized = cv2.resize(image, (400, 400))

        # Create a blob
        blob = cv2.dnn.blobFromImage(image_resized, 0.007843, (300, 300), (127.5, 127.5, 127.5))

        # ----------- DETECTIONS AND PREDICTIONS -----------
        net.setInput(blob)
        detections = net.forward()

        archivo=open("arrays.txt","w")
        archivo.close

        for detection in detections[0][0]:
            
            if detection[2] > 0.30:
                label = classes[detection[1]]
                box = detection[3:7] * [width, height, width, height]
                x, y, w, h = int(box[0]), int(box[1]), int(box[2]), int(box[3])
                cX = x+((w-x)//2)
                cY = y+((h-y)//2)
                
                rectangle = cv2.rectangle(image, (x, y), (w, h), (0, 255, 0), 2)
                cv2.putText(image, "Conf: {:.2f}".format(detection[2] * 100), (x, y - 5), 1, 1.2, (255, 0, 0), 2)
                cv2.putText(image, label, (x, y - 25), 1, 1.2, (255, 0, 0), 2)  #agregar distancia
        
                detec2=np.append(detection,[cX, cY])
                archivo=open("arrays.txt","a")
                archivo.write("["+ "\n")
                for i in range(len(detec2)):
                    archivo.write(str(detec2[i])+"\n")
                archivo.write("]"+"\n")
                archivo.close
                
        cv2.imshow("Image", image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    def upload(self):
        datos1 = []
        datos = []
        archivo = open("base_datos.txt", "r")
        data = archivo.read()
        texto = data.replace("[\n", "").replace("\n]", "]").replace("\n", " ").replace("] ", "\n").replace("]", "")
        archivo.close()

        archivo = open("base_datos2.txt", "w")
        data = archivo.write(texto)
        archivo.close()

        archivo = open("base_datos2.txt", "r")
        lineas = archivo.readlines()
        for linea in lineas:
            datos1.append(linea.strip('\n'))
        for dato in datos1:
            datos.append(dato.split(" "))
        for dato in datos:
            for i in range(len(dato)):
                if i == 0:
                    pass
                else: 
                    dato[i] = float(dato[i])
        archivo.close()

        for dato in datos:
            dato[1] = round(dato[1], 6)
            dato[2] = round(float(dato[6]), 3)
            dato[3] = round(float(dato[5]), 2)
            dato[4] = round(float(dato[4]), 2)
            dato.pop(6)
            dato.pop(5)
            dato = tuple(dato)

        #CREDENCIALES PARA LA CONEXIÓN A MYSQL (CAMBIAR DE ACUERDO A LA COMPU)
        my_host = "localhost"
        my_user = "root"
        my_password = "valiente360"
        my_database = "db_prueba"

        #SUBIR DATOS A DATABASE
        try:
            connection = mysql.connector.connect(
                host=my_host,
                user=my_user,
                passwd=my_password,
                db=my_database
                )
            cur = connection.cursor()
            sql_1 = "INSERT INTO sensor (marca, modelo) VALUES (%s, %s)"
            val_1 = ("genérica", "HC-SR04")
            cur.execute(sql_1, val_1)
            sql_2 = "INSERT INTO camara (marca, modelo) VALUES (%s, %s)"
            val_2 = ("genérica", "ESP32-CAM con cámara OV2640")
            cur.execute(sql_2, val_2)
            sql_3 = "INSERT INTO arduinoboard (marca, modelo) VALUES (%s, %s)"
            val_3 = ("genérica", "ARDUINO UNO")
            cur.execute(sql_3, val_3)
            sql_4 = "INSERT INTO obstaculos (label, confianza, distancia, angulo_vertical, angulo_horizontal) VALUES (%s, %s, %s, %s, %s)"
            val_4 = datos
            cur.executemany(sql_4, val_4)
            connection.commit()
            print("Data was uploaded successfully")
        except Error as error:
            print("Error loading Obstacles: {}".format(error))
        finally:
            if (connection.is_connected()):
                cur.close()
                connection.close()
                print("MySQL connection is closed")

    def get_info(self):
        #CREDENCIALES DE ACCESO
        my_host = "localhost"
        my_user = "root"
        my_password = "valiente360"
        my_database = "db_prueba"

        # LISTA VACÍA PARA LAS DISTANCIAS
        distancias = []
        
        try:
            connection = mysql.connector.connect(
                host=my_host,
                user=my_user,
                passwd=my_password,
                db=my_database
                )
            cur = connection.cursor()
            cur.execute("SELECT * FROM obstaculos")
            for registro in cur.fetchall():
                Distancia = registro[3]
                distancias.append(Distancia)
            print("Data has been retrieved successfully")
        except Error as error:
            print("Error al ejecutar el procedimiento: {}".format(error))
        finally:
            if (connection.is_connected()):
                cur.close()
                connection.close()
                print("MySQL connection is closed")

        #  "distancias" es la lista con las distancias de la base de datos
        return distancias

    def get_image(self):
        distancias = self.get_info()
        general = self.obtener_lista()

        prototxt = "model/MobileNetSSD_deploy.prototxt.txt"
        model = "model/MobileNetSSD_deploy.caffemodel"
        # Class labels
        classes = {0:"background", 1:"airplane", 2:"bicycle",
                3:"bird", 4:"boat",
                5:"bottle", 6:"bus",
                7:"car", 8:"cat",
                9:"chair", 10:"cow",
                11:"diningtable", 12:"dog",
                13:"horse", 14:"motorbike",
                15:"person", 16:"pottedplant",
                17:"sheep", 18:"sofa",
                19:"train", 20:"tvmonitor"}

        # Load the model
        net = cv2.dnn.readNetFromCaffe(prototxt, model)

        # ----------- READ THE IMAGE AND PREPROCESSING -----------
        image = cv2.imread("Camara.jpg")
        height, width, _ = image.shape
        image_resized = cv2.resize(image, (300, 300))

        blob = cv2.dnn.blobFromImage(image_resized, 0.007843, (300, 300), (127.5, 127.5, 127.5))

        net.setInput(blob)
        detections = net.forward()

        for i in range(len(general)):
            cv2.putText(image, f'Objeto:', (int(general[i][2])-20,int(general[i][3])  - 40), 1, 1.1, (57, 255, 20), 2)
            cv2.putText(image, f'{classes[int(general[i][0])]}', (int(general[i][2])-20,int(general[i][3])  - 20), 1, 1.1, (255, 0, 0), 2)
            cv2.putText(image,f'Dist:' ,(int(general[i][2])-25, int(general[i][3]) ), 1, 1.1, (57, 255, 20), 2)
            cv2.putText(image,f'{distancias[i]}' ,(int(general[i][2]+20), int(general[i][3])), 1, 1.1, (255, 0, 0), 2)

        cv2.imshow("Image", image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    
    def control_bt_normal(self):
        self.showNormal()
        self.bt_normal.hide()
        self.bt_maximize.show()

    def control_bt_maximize(self):
        self.showMaximized()
        self.bt_maximize.hide()
        self.bt_normal.show()
    
    def resizeEvent(self, event):
        rect = self.rect()
        self.grip.move(rect.right() - self.gripSize, rect.bottom() - self.gripSize)
    
    def mousePressEvent(self, event):
        self.click_posicion = event.globalPos()
    
    def mover_ventana(self,event):
        if self.isMaximized() == False:
            if event.buttons() == QtCore.Qt.LeftButton:
                self.move(self.pos() + event.globalPos() - self.click_posicion)
                self.click_posicion = event.globalPos()
                event.accept()
        if event.globalPos().y() <= 5 or event.globalPos().x() <= 5 :
            self.showMaximized()
            self.bt_maximize.hide()
            self.bt_normal.show()
        else:
            self.showNormal()
            self.bt_normal.hide()
            self.bt_maximize.show()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    my_app = MyApp()
    my_app.show()
    sys.exit(app.exec_())
