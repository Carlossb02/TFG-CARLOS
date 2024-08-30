#include <DHT.h>
#include <ESP8266WiFi.h>
#include <ArduinoWebsockets.h>
#include <ESP8266mDNS.h>

//pines
#define DHTPIN D2
#define WATER_SENSOR_PIN A0
#define WATER_SENSOR_POWER D1
#define DHTTYPE DHT11
#define LED_PIN D3
DHT dht(DHTPIN, DHTTYPE);

//configuracion de la red
const char* ssid = "";
const char* password = ""; 
String server_ip;
uint16_t server_port = 5000;
const char* target_service_name = "GardenControllerServer";

using namespace websockets;
WebsocketsClient webSocket;
bool isConnected = false;

void connectWiFi() {
  Serial.println();
  Serial.print("Conectando a ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("WiFi conectado");
  Serial.println("Dirección IP: ");
  Serial.println(WiFi.localIP());
}

void discoverServer() {
  Serial.println("Buscando el servidor...");
  
  //buscar el servidor
  int n = MDNS.queryService("http", "tcp");
  
  if (n == 0) {
    Serial.println("Servidor no encontrado");
  } else {
    Serial.println("Servidor encontrado: ");
    for (int i = 0; i < n; i++) {
      Serial.print(i + 1);
      Serial.print(": ");
      Serial.print(MDNS.hostname(i));
      Serial.print(" (");
      Serial.print(MDNS.IP(i));
      Serial.print(":");
      Serial.print(MDNS.port(i));
      Serial.println(")");
      
      //guardar datos del servidor
      server_ip = MDNS.IP(i).toString();
      server_port = MDNS.port(i);
      break;
      }
    }
    
    //si no se ha encontrado, buscar en bucle
    if (server_ip.length() == 0) {
      discoverServer();
    }
  }


void connectWebSocket() {
  Serial.println("Conectando al servidor WebSocket...");
  if (webSocket.connect(server_ip, server_port, "/")) {
    isConnected = true;
    Serial.println("Conectado al servidor WebSocket");
    digitalWrite(LED_PIN, HIGH); //encender led si se conecta
  } else {
    isConnected = false;
    Serial.println("Error al conectar al servidor WebSocket");
    digitalWrite(LED_PIN, LOW); //apaga el led si se desconecta
  }
}

void setup() {
  Serial.begin(9600);

  //configuracion led
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW); 

  //conectar wifi
  connectWiFi();

    //iniciar mdns
  if (MDNS.begin("Arduino")) {
    Serial.println("MDNS iniciado");
  } else {
    Serial.println("Error al iniciar MDNS");
    while(1) {
      delay(1000);
    }
  }

  discoverServer();

  //inicializamos el sensor DHT11 y el de agua
  dht.begin();
  pinMode(WATER_SENSOR_PIN, INPUT);
  pinMode(WATER_SENSOR_POWER, OUTPUT);
  digitalWrite(WATER_SENSOR_POWER, LOW);

  //inicializamos el WebSocket
  webSocket.onMessage([](WebsocketsMessage message) {
    Serial.print("Mensaje recibido: ");
    Serial.println(message.data());
  });

  connectWebSocket();
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    connectWiFi();
  }

  if (!webSocket.available() || !isConnected) {
    Serial.print(server_ip);
    connectWebSocket();
  }

  webSocket.poll();

  //leemos la humedad relativa
  float h = dht.readHumidity();
  //leemos la temperatura
  float t = dht.readTemperature();

  digitalWrite(WATER_SENSOR_POWER, HIGH);
  delay(50);
  int agua = analogRead(WATER_SENSOR_PIN);
  digitalWrite(WATER_SENSOR_POWER, LOW);

  //comprobamos si ha habido algún error en la lectura
  if (isnan(h) || isnan(t)) {
    Serial.println("Error obteniendo los datos del sensor DHT11");
    return;
  }

  String nivel;
  Serial.println(agua);
  switch (agua) {
      case 0 ... 14:  //Nivel bajo
          nivel="Bajo";
          break;
      case 15 ... 136: //Nivel medio
          nivel="Medio";
          break;
      case 137 ... 200:  //Nivel alto
          nivel="Alto";
          break;
      default:
          nivel="Error"; 
          break;
  }

  //formateamos los datos en diccionario de python
  String data = "{\"Humedad\": " + String(h) + ", \"Temperatura\": " + String(t)+ ", \"Nivel de agua\": " + "\"" + String(nivel)+ "\"" + "}";
  Serial.println(data);

  //enviamos los datos al servidr WebSocket
  if (webSocket.available() && isConnected) {
    Serial.println("Enviando datos: " + data);
    webSocket.send(data);
  } else {
    //si el WebSocket no disponible o no conectado, apagamos LED
    digitalWrite(LED_PIN, LOW);
  }

  delay(2000);  //esperamos 2 segundos antes de la proxima lectura
}
