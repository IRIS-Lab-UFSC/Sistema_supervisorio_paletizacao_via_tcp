import socket
import threading
import customtkinter as ctk
import tkinter as tk
import math

INTERFACE = "system"
THEME = "blue"

ctk.set_appearance_mode(INTERFACE)
ctk.set_default_color_theme(THEME)

class PalletizingGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        program_title = "Palletizing System for the UR10 Robot"
        size = "1100x700"

        self.title(program_title)
        self.geometry(size)

        self.robot_socket = None
        self.server_socket = None
        self.conn = None

        self.heights = []
        self.rotations = []

        self.layout()
        self.pallet_layout()
    @staticmethod
    def create_textbox(parent,text_frame="",value="", textvariable=None):
  
       frame = ctk.CTkFrame(parent, fg_color="transparent")
       frame.pack(fill="x", padx=15, pady=2)
       ctk.CTkLabel(frame, text=text_frame, width=110, anchor="w").pack(side="left")
       entry = ctk.CTkEntry(frame, placeholder_text=value, textvariable=textvariable)
       entry.pack(side="right", fill="x", expand=True)
       return entry
    @staticmethod
    def create_radio_button(parent, text, options, var):
       frame = ctk.CTkFrame(parent, fg_color="transparent")
       frame.pack(fill="x", padx=15, pady=8)
       ctk.CTkLabel(frame, text=text, width=110, anchor="w", font=ctk.CTkFont(weight="bold")).pack(side="left")

       radio_frame = ctk.CTkFrame(frame, fg_color="transparent")
       radio_frame.pack(side="right", fill="x", expand=True)

       for mode in options:
        rb = ctk.CTkRadioButton(radio_frame, text=mode, value=mode, variable=var).pack(side="left", padx=10)

    def create_button(self,parent, text, color, command):
       frame = ctk.CTkFrame(parent, fg_color="transparent")
       frame.pack(fill="x", padx=15, pady=5)
       ctk.CTkButton(frame, text=text, fg_color=color, width=80, command=command).pack(side="left", padx=2, expand=True)



    def layout(self):
       for column in range(3):
        self.grid_columnconfigure(column, weight=1)
       self.grid_rowconfigure(0, weight=1)
       
       left_frame = ctk.CTkFrame(self, corner_radius=5)
       left_frame.grid(row=0, column=0, padx=10, pady=15, sticky="nsew")
      
       frame_input = ctk.CTkFrame(left_frame, fg_color="#e7b3b3", corner_radius=8)
       frame_input.pack(fill="x", padx=15, pady=(10, 5))

       lbl_input = ctk.CTkLabel(
            frame_input, 
            text="Exemplo de Input:\n• Velocidade, Aceleração, Blend (ex: 0.5,0.5,0.05)\n ", 
            font=ctk.CTkFont(size=13), 
            justify="left"
        )
       lbl_input.pack(padx=10, pady=8)

       rede = ctk.CTkLabel(left_frame, text="Configurações de Rede", font=ctk.CTkFont(size=15, weight="bold"))
       rede.pack(pady=5)
        

       self.robot_ip=self.create_textbox(left_frame,"IP do Robô:", "192.168.0.10")

       self.ip_pc=self.create_textbox(left_frame,"IP do PC:", "192.168.0.103")

       ctk.CTkLabel(left_frame, text="Parâmetros de Movimento", font=ctk.CTkFont(size=15, weight="bold")).pack(pady=10)

    
       self.entry_movm=self.create_textbox(left_frame,"Velocidade, Aceleração, Blend: ", "0.5,0.5,0.5")

      
       self.input_var = ctk.StringVar()

       self.input_var.trace_add("write", self.create_layers_boxes)
       self.params_grid = self.create_textbox(left_frame, "Camada, Linha e Coluna: ", "3,4,3",textvariable=self.input_var)
       
       self.aprox=self.create_textbox(left_frame,"Altura de aproximação: ", 0.1)

       self.mode_var = ctk.StringVar(value="FIXO")

       self.modes=self.create_radio_button(left_frame, text="Modo de operação:", options=["FIXO","FREEDRIVE"], var=self.mode_var)
       

       self.button_connection = ctk.CTkButton(left_frame, text="Conectar e Enviar Script", command=self.start_connection)
       self.button_connection.pack(fill="x", padx=15, pady=3)
     
       self.logbox = ctk.CTkTextbox(left_frame, height=120)
       self.logbox.pack(fill="both", padx=15, pady=5, expand=True)

     
       button_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
       button_frame.pack(fill="x", padx=15, pady=5)

       ctk.CTkButton(button_frame, text="STOP", fg_color="red", width=80, 
        command=lambda: self.send_emergency_request("STOP")).pack(side="left", padx=2, expand=True)
       ctk.CTkButton(button_frame, text="PAUSE", fg_color="orange", width=80, 
        command=lambda: self.send_emergency_request("PAUSE")).pack(side="left", padx=2, expand=True)
      
       
     
       self.central_frame = ctk.CTkScrollableFrame(self, label_text="Configuração por Layer")
       self.grid_columnconfigure(1, minsize=350) 
       self.central_frame.grid(row=0, column=1, padx=10, pady=15, sticky="nsew")

     
       pallet_preview = ctk.CTkFrame(self, corner_radius=10)
       pallet_preview.grid(row=0, column=2, padx=10, pady=15, sticky="nsew")
        
       ctk.CTkLabel(pallet_preview, text="Visualização Padrão das Caixas", font=ctk.CTkFont(size=15, weight="bold")).pack(pady=10)

       self.view_layer_var = ctk.StringVar(value="Layer 1")
       self.seletor_view = ctk.CTkOptionMenu(pallet_preview, variable=self.view_layer_var, values=["Layer 1"])
       self.seletor_view.pack(pady=5, padx=20, fill="x")
       
   
       self.view_layer_var.trace_add("write", self.pallet_layout)

       self.canvas = tk.Canvas(pallet_preview, width=420, height=420, bg="#b2ecaf", highlightthickness=0)
       self.canvas.pack(padx=20, pady=10)
        
       self.countboxes = ctk.CTkLabel(pallet_preview, text="Total de caixas por layer: 0", font=ctk.CTkFont(size=15))
       self.countboxes.pack(pady=5)
    def create_layers_boxes(self, *args):
    
        palletPosition = self.input_var.get().strip()
        
      
        input_data = palletPosition.split(',')
     
        first_param = input_data[0].strip()
        
  
        if first_param=="" or not first_param.isdigit():
            return
            
        num_layers = int(first_param)
        if num_layers < 1:
            return
        
        for widget in self.central_frame.winfo_children():
            widget.destroy()
            
        self.heights.clear()
        self.rotations.clear()

      
        for i in range(num_layers):
            label = ctk.CTkLabel(self.central_frame, text=f" LAYER {i+1}", font=ctk.CTkFont(size=12,weight="bold"), text_color="#1f538d")
            label.pack(pady=(8, 2))

         
            
            frame_height = ctk.CTkFrame(self.central_frame, fg_color="transparent")
            frame_height.pack(fill="x", padx=10, pady=2) 
            ctk.CTkLabel(frame_height, text=f"Alt. Z (L) [m]:", width=140, anchor="w").pack(side="left")
            if i==0:
                fixed_height = ctk.CTkLabel(frame_height, text="0.0", anchor="w")
                fixed_height.pack(side="right", fill="x", expand=True)
                dummy_entry = ctk.StringVar(value="0.0")
                self.heights.append(dummy_entry)
            else:

                entry_height = ctk.CTkEntry(frame_height)
                entry_height.insert(0, "0.05")
                entry_height.pack(side="right", fill="x", expand=True)
                self.heights.append(entry_height) 

         
            frame_rot = ctk.CTkFrame(self.central_frame, fg_color="transparent")
            frame_rot.pack(fill="x", padx=10, pady=2)
            ctk.CTkLabel(frame_rot, text="Rotação Z [rad]:", width=140, anchor="w").pack(side="left")

            
  
            rot_var = ctk.StringVar(value="0.0")
            entry_rotation = ctk.CTkEntry(frame_rot, textvariable=rot_var)
            
       
            rot_var.trace_add("write", self.pallet_layout)
            
            entry_rotation.pack(side="right", fill="x", expand=True)
            self.rotations.append(entry_rotation)
            
 
        layers_options = [f"Layer {i+1}" for i in range(num_layers)]
        self.seletor_view.configure(values=layers_options)
    
        self.pallet_layout()

    def pallet_layout(self, *args):
        self.canvas.delete("all") 
        palletPosition = self.input_var.get().strip()
        
    
        input_data = palletPosition.split(',')
        

        if len(input_data) < 3:
            return
            
        if not input_data[1].strip().isdigit() or not input_data[2].strip().isdigit():
            return
        
        rows = int(input_data[1].strip())
        columns = int(input_data[2].strip())

        self.countboxes.configure(text=f"Total de caixas por layer: {rows * columns}")

        selected_layer = self.view_layer_var.get()

        try:
            layer_idx = int(selected_layer.split()[1]) - 1
        except (IndexError, ValueError):
            layer_idx = 0  

        rotation=0.0
        if layer_idx < len(self.rotations):
            val_rot = self.rotations[layer_idx].get().strip()
            try:
                rotation = float(val_rot)
            except ValueError:
                rotation = 0.0
            

        self.canvas.create_rectangle(20, 20, 390, 390, outline="#555555", width=2, fill="#1e1e1e")

        side_length = 320
        box_width = (side_length / max(columns, 2)) * 0.5
        box_height = (side_length / max(rows, 2)) * 0.9


        for row in range(rows):
            for column in range(columns):
           
                cx = 40 + (side_length / max(columns, 1)) * (column + 0.5)
                cy = 40 + (side_length / max(rows, 1)) * (row + 0.5)

                points = [
                    (-box_width/2, -box_height/2),
                    (box_width/2, -box_height/2),
                    (box_width/2, box_height/2),
                    (-box_width/2, box_height/2)
                ]
    
                rotated_points = []
                for px, py in points:
                    rx = px * math.cos(rotation) - py * math.sin(rotation)
                    ry = px * math.sin(rotation) + py * math.cos(rotation)
                    rotated_points.append(cx + rx)
                    rotated_points.append(cy + ry)

                self.canvas.create_polygon(rotated_points, fill="#1f538d", outline="#3a7ebf", width=1)
                self.canvas.create_text(cx, cy, text=f"{row},{column}", fill="white", font=ctk.CTkFont(size=13))
    def log(self, message):
        self.logbox.insert("end", message + "\n")
        self.logbox.see("end")

    def configure_ip_addresses(self):
        try:
            with open("palletizing.script", "r") as f:
                script = f.read()
            new_script= script.replace('socket_open("192.168.0.100", 5000, "pc")',
            f'socket_open("{self.ip_pc.get()}", 5000, "pc")')

            return new_script
        except Exception as error:
            self.log(f"Erro ao ler script: {error}")
            return None

    def start_connection(self):
        threading.Thread(target=self.network_manager, daemon=True).start()
    
    def network_manager(self):
        try:
            script = self.configure_ip_addresses()
            if script is None:
                self.log("Script inválido ou não encontrado") 
                return
    
            self.log("Conectando ao Robô...")
            self.robot_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.robot_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.robot_socket.connect((self.robot_ip.get(), 30002))
    
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(("0.0.0.0", 5000))
            self.server_socket.listen(1)
    
            self.robot_socket.sendall(script.encode("utf-8"))
            self.log("Script enviado! Aguardando retorno do robô...")
    
            self.conn, addr = self.server_socket.accept()
            self.log(f"Robô conectado via IP: {addr[0]}")
    
            threading.Thread(target=self.process_robot_message, daemon=True).start()
            self.send_palletizing_parameters()
    
        except Exception as error:
            self.log(f"Erro na conexão: {error}")

    def send_palletizing_parameters(self):

        self.conn.sendall(f"({self.entry_movm.get()})".encode('utf-8'))
        self.conn.sendall(f"({self.params_grid.get()})".encode('utf-8'))
        self.conn.sendall(f"({self.aprox.get()})".encode('utf-8'))
    
        heights_str = ",".join([i.get() for i in self.heights]) if self.heights else "0.0"  
        self.conn.sendall(f"({heights_str})".encode('utf-8')) 
    
        rotations_str = ",".join([i.get() for i in self.rotations])
        self.conn.sendall(f"({rotations_str})".encode('utf-8'))
    
        operation_mode = self.mode_var.get()
        self.conn.sendall(f"{operation_mode}\n".encode('utf-8'))
        self.log(f"Parâmetros enviados! Operando em modo: {operation_mode}")

    def process_robot_message(self):
            while True:
                try:
                    data = self.conn.recv(1024)
                    if not data: break   
                    self.log(f"[ROBÔ]: {data.decode('utf-8').strip()}")
                except Exception as error:
                    self.log(f"[ERRO]: Conexão perdida ({error})")
                    break
    def send_emergency_request(self, cmd): 
        if self.conn:
            try:
                self.conn.sendall((cmd + "\n").encode('utf-8'))
                self.log(f"Comando {cmd} enviado.")
            except Exception as e:
                self.log(f"Erro ao enviar {cmd}: {e}")
    
    def on_closing(self):
        try:
            if self.conn: self.conn.close()
            if self.server_socket: self.server_socket.close()
            if self.robot_socket: self.robot_socket.close()
        except: pass
        self.destroy()                         

if __name__ == "__main__":
    app = PalletizingGUI()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()