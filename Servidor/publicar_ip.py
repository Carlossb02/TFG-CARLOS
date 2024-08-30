from zeroconf import ServiceInfo, Zeroconf
import socket


def publicar_ip():
    service_type = "_http._tcp.local."
    service_name = "GardenControllerServer._http._tcp.local."
    server_ip = socket.gethostbyname(socket.gethostname())
    server_port = 5000

    #informacion del servicio
    info = ServiceInfo(
        type_=service_type,
        name=service_name,
        addresses=[socket.inet_aton(server_ip)],
        port=server_port,
        properties={},
        server=socket.gethostname()
    )

    #anunciar el servicio en la red
    zeroconf = Zeroconf()
    zeroconf.register_service(info)

    print(f"Servicio anunciado: {service_name} en {server_ip}:{server_port}")
