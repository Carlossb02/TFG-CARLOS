import asyncio
import time
import ssl
import websockets
import os
import json
import datetime


Ejemplo_conectados = {"192.168.1.20": True, "192.168.1.30": False}
conectados = {}

Ejemplo_datos = {"192.168.1.20": [40.0, 24.0, "Bajo"], "192.168.1.30": [None, None, None]}
datos = {}


async def manejar_conexiones(websocket):
    global conectados
    global datos
    ip_cliente = websocket.remote_address[0]

    #Para asegurar que los datos se obtienen a tiempo real, cerramos la conexión si se dejan de recibir
    #datos o tardan más de lo que tarda el sensor DHT11 en obtener una lectura de datos.
    async def comprobar_socket():
        while True:
            await asyncio.sleep(2)
            if (datetime.datetime.now() - last_message_time).total_seconds() > 3:
                print(f"SERVER: error, tiempo de espera excedido para {ip_cliente}, cerrando la conexión")
                if ip_cliente in conectados.keys():
                    conectados[ip_cliente]=False
                    datos[ip_cliente]=[None, None, None]

                await websocket.close()
                return



    try:
        async for message in websocket:
            with open("microcontroladores.json", "r") as file:
                devices = json.loads(file.read())

            with open("dispositivos.json", "r") as file:
                headsets = json.loads(file.read())

            if ip_cliente in devices.values():
                last_message_time = datetime.datetime.now()
                asyncio.create_task(comprobar_socket())
                print(f"DEVICE: solicitud de {ip_cliente} aceptada")
                print(f"DEVICE: datos recibidos: {message}")
                telemetria = json.loads(message)
                conectados[ip_cliente]=True
                datos[ip_cliente]=[telemetria["Humedad"], telemetria["Temperatura"], telemetria["Nivel de agua"]]
                print(datos, conectados)
                telemetria["Timestamp"] = datetime.datetime.now().isoformat()
                guardar_json(telemetria, ip_cliente)

                #actualizamos el ultimo tiempo de actividad
                last_message_time = datetime.datetime.now()



            elif ip_cliente in headsets.values():
                device_ip=devices[message]
                print("HEADSET: solicitados datos de", device_ip)
                asyncio.create_task(enviar_telemetria_async(device_ip, websocket))

            else:
                raise Exception("dispositivo desconocido " + ip_cliente)

    except websockets.ConnectionClosed:
        print(f"DEVICE: {ip_cliente} desconectado")
    except Exception as e:
        print("DEVICE: error, cerrando conexión", e)
    finally:
        conectados[ip_cliente] = False
        datos[ip_cliente] = [None, None, None]


async def enviar_telemetria_async(device_ip, websocket):
    try:
        while device_ip in conectados and conectados[device_ip]:
            texto_send=f"Humedad: {datos[device_ip][0]}%\nTemperatura:{datos[device_ip][1]}º\nNivel de agua:{datos[device_ip][2]}"
            await websocket.send(texto_send)
            await asyncio.sleep(0.1)
        #Device desconectado
        await websocket.send("Device sin conexión")
        await asyncio.sleep(1)
        await websocket.close()
    except websockets.ConnectionClosed:
        print(f"Conexión cerrada para {device_ip}")


def guardar_json(datos, client):
    filename = "telemetry_" + client + ".json"

    if os.path.exists(filename):
        with open(filename, "r") as file:
            existing_data = json.load(file)

        existing_data.append(datos)

        #solo guardamos los últimos 20
        if len(existing_data) > 20:
            existing_data = existing_data[-20:]

        #guardamos
        with open(filename, "w") as file:
            json.dump(existing_data, file)
    else:
        #si no existe, creamos el fichero
        with open(filename, "w") as file:
            json.dump([datos], file)


async def server_run():
    ip="0.0.0.0"
    port=5000
    try:
        """ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        try:
            ssl_context.load_cert_chain(certfile="cert.pem", keyfile="key.pem", password="1234")
        except Exception as e:
            print(f"SERVER: Error cargando certificados ({e})")
            return
        async with websockets.serve(manejar_conexiones, ip, port, ssl=ssl_context):"""
        async with websockets.serve(manejar_conexiones, ip, port):
            print(f"SERVER: Servidor WebSocket iniciado en {ip}:{port}")
            await asyncio.Future()
    except Exception as e:
        print(f"SERVER: Error al iniciar el servidor: {e}")


if __name__ == "__main__":
    asyncio.run(server_run())
