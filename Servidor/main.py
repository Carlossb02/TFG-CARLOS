import tkinter as tk
from tkinter import scrolledtext, messagebox
import json
import os
import threading
import sys
from tkinter import ttk
from server import *
from publicar_ip import *


class JSONEditorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AR Garden Controller Server")
        self.root.configure(background="#00a6ff")
        self.running = False
        self.create_widgets()
        self.t1 = None
        self.redirect_msg()
        self.t1 = threading.Thread(target=self.start_server, daemon=True)
        self.t1.start()
        self.selector=None
        self.telemetry_files=[]


    def redirect_msg(self):
        sys.stdout = Redirigir_msg(self.console)

    def create_widgets(self):
        self.title_label = tk.Label(self.root,background="#00a6ff", text="Consola", font=("Helvetica", 16, "bold"), fg="white")
        self.title_label.pack(pady=10)

        #Consola
        self.console = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, height=10)
        self.console.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        print("Consola Iniciada...\n")

        self.title_label2 = tk.Label(self.root,background="#00a6ff", text="Editor", font=("Helvetica", 16, "bold"), fg="white")
        self.title_label2.pack(pady=10)

        #Frame de botones
        self.button_frame = tk.Frame(self.root, background="#00a6ff")
        self.button_frame.pack(pady=10, fill=tk.X)

        #Botón de Dispositivos
        self.dispositivos= tk.Button(self.button_frame, text="Dispositivos", command=lambda: self.open_json("dispositivos.json"), background="white", fg="black", border=1)
        self.dispositivos.pack(side=tk.LEFT, padx=5)

        #Botón de Microcontroladores
        self.microcontroladores = tk.Button(self.button_frame, text="Microcontroladores", command=lambda: self.open_json("microcontroladores.json"), background="white", fg="black", border=1)
        self.microcontroladores.pack(side=tk.LEFT, padx=5)

        self.opciones = tk.Label(self.button_frame, background="#00a6ff", text="Telemetrías:", font=("Helvetica", 9, "bold"), fg="white")
        self.opciones.pack(side=tk.LEFT, padx=5)

        self.combo = ttk.Combobox(self.button_frame, state="readonly", background="white")
        self.combo.pack(side=tk.LEFT, padx=5)

        #Botón de Borrar
        self.delete_button = tk.Button(self.button_frame, text="Borrar", command=self.remove_telemetry, background="white", fg="black", border=1)
        self.delete_button.pack(side=tk.LEFT, padx=5)


        #Textos json
        self.json_text = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, height=15)
        self.json_text.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        #Botón de Guardar
        self.save_button = tk.Button(self.root, text="Guardar", command=self.save_json, background="white", fg="black", border=1)
        self.save_button.pack(pady=10)



        self.list_json_files()

    def list_json_files(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        json_files = [f for f in os.listdir(current_dir) if f.endswith('.json')]
        self.telemetry_files=[]

        for file in json_files:
            if file.startswith('telemetry'):
                self.telemetry_files.append(file)


        self.combo["values"]=self.telemetry_files
        self.combo.bind("<<ComboboxSelected>>", self.open_json_telemetry)


    def open_json(self, file_path):
        self.current_file = file_path
        self.selector = file_path
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                self.json_text.config(state=tk.NORMAL)
                self.json_text.delete(1.0, tk.END)
                self.json_text.insert(tk.END, json.dumps(data, indent=4))
                print(f"SERVER: archivo {file_path} cargado exitosamente")
        except:
                print("SERVER: error al guardar el archivo")

    def open_json_telemetry(self, event):
        try:
            with open(self.combo.get(), 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.json_text.config(state=tk.NORMAL)
            self.json_text.delete(1.0, tk.END)
            self.json_text.insert(tk.END, json.dumps(data, indent=4))
            self.json_text.config(state=tk.DISABLED)
            print(f"SERVER: telemetría cargada correctamente")
            self.selector="telemetria"
        except:
            print("SERVER: error al abrir el archivo")

    def save_json(self):
        try:
            if self.selector and self.selector!="telemetria":
                data = json.loads(self.json_text.get(1.0, tk.END))
                with open(self.current_file, 'w', encoding='utf-8') as file:
                    json.dump(data, file, indent=4)
                    print(f"SERVER: archivo {self.current_file} guardado correctamente")
            else:
                print("SERVER: no hay datos que guardar")
        except:
            print("SERVER: error al guardar el archivo")

    def remove_telemetry(self):
        if self.selector=="telemetria":
            confirmar = messagebox.askquestion("Borrar telemetría", "¿Estás seguro de que quieres borrar el archivo?", type=messagebox.YESNO)
            if confirmar==messagebox.YES:
                os.remove(self.combo.get())
                print("SERVER: telemetría borrada satisfactoriamente")
                self.list_json_files()
                self.combo["values"] = self.telemetry_files
                self.combo.bind("<<ComboboxSelected>>", self.open_json_telemetry)
        else:
            print("SERVER: error, sólo puede borrar telemetrías")

    def start_server(self):
        publicar_ip()
        asyncio.run(server_run())



class Redirigir_msg:
    def __init__(self, console_widget):
        self.console_widget = console_widget

    def write(self, text):
        self.console_widget.insert(tk.END, text)
        self.console_widget.see(tk.END)

    def flush(self):
        pass


if __name__ == "__main__":
    root = tk.Tk()
    app = JSONEditorApp(root)
    root.mainloop()
