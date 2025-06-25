import tkinter as tk
from tkinter import messagebox
import socket
import threading
import json
import os
import pygame

# --- Configuración de la Red ---
HOST = '0.0.0.0' # Escucha en todas las interfaces disponibles
PORT = 12345     # Debe coincidir con el puerto en la Raspberry Pi Pico W

# --- Archivos de Datos ---
PROFILES_FILE = 'player_profiles.json'
RANKINGS_FILE = 'game_rankings.json'

# --- Datos del Juego ---
current_player = None
current_score = 0
player_profiles = {}
game_rankings = []

# --- Variables para la Interfaz de Juego ---
seven_seg_display_label = None
excess3_output_label = None
excess3_valid_label = None
current_score_label = None
current_player_label = None

# --- Funciones de Carga/Guardado de Datos ---
def load_data(filename, default_value):
    if os.path.exists(filename):
        try:
            with open(filename, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"Error al decodificar JSON en {filename}. Se usará el valor por defecto.")
            return default_value
    return default_value

def save_data(filename, data):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)

# --- Funciones de Música ---
def play_music(file_path):
    if not pygame.mixer.get_init():
        pygame.mixer.init()
    try:
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play(-1) # -1 para loop infinito
    except pygame.error as e:
        print(f"Error al cargar o reproducir música: {e}. Asegúrate de que el archivo '{file_path}' existe y es válido.")

def stop_music():
    if pygame.mixer.get_init():
        pygame.mixer.music.stop()

# --- Funciones de la GUI ---

def show_main_menu():
    for widget in root.winfo_children():
        widget.destroy()

    # Título
    tk.Label(root, text="Buttons, Lights and Sounds - Project II", font=("Courier New", 24, 'bold'), fg="#e94560", bg="#1a1a2e").pack(pady=40)

    # Botones
    button_frame = tk.Frame(root, bg="#1a1a2e")
    button_frame.pack(pady=50)

    create_ps1_button(button_frame, "◆ SELECT PLAYER", show_profile_selection).pack(pady=10)
    create_ps1_button(button_frame, "◆ CREATE NEW PLAYER", show_create_profile).pack(pady=10)
    create_ps1_button(button_frame, "◆ RANKINGS", show_rankings).pack(pady=10)
    create_ps1_button(button_frame, "◆ EXIT", root.quit).pack(pady=10)

    play_music("Avengers.mp3") # Asegúrate de tener este archivo de música

def create_ps1_button(parent, text, command, width=25, height=2):
    # Reutiliza la función de botón estilo PS1 de tu código original
    button = tk.Button(
        parent,
        text=text,
        command=command,
        font=('Courier New', 12, 'bold'),
        bg='#0f3460',
        fg='#f5f5f5',
        activebackground='#e94560',
        activeforeground='#f5f5f5',
        relief='raised',
        borderwidth=3,
        width=width,
        height=height,
        cursor='hand2'
    )
    def on_enter(e):
        button.config(bg='#e94560')
    def on_leave(e):
        button.config(bg='#0f3460')
    button.bind("<Enter>", on_enter)
    button.bind("<Leave>", on_leave)
    return button

def show_profile_selection():
    for widget in root.winfo_children():
        widget.destroy()

    tk.Label(root, text="PLAYER SELECT", font=("Courier New", 20, 'bold'), fg="#e94560", bg="#1a1a2e").pack(pady=20)

    if not player_profiles:
        tk.Label(root, text="No profiles created. Please create a new one.", font=("Courier New", 12), fg="#f5f5f5", bg="#1a1a2e").pack(pady=10)
        create_ps1_button(root, "BACK", show_main_menu).pack(pady=20)
        return

    profile_list_frame = tk.Frame(root, bg="#16213e", relief='raised', bd=2)
    profile_list_frame.pack(pady=10, padx=50, fill='both', expand=True)

    profile_listbox = tk.Listbox(
        profile_list_frame,
        font=('Courier New', 12),
        bg='#0f3460',
        fg='#f5f5f5',
        selectbackground='#e94560',
        height=8
    )
    profile_listbox.pack(padx=10, pady=10, fill='both', expand=True)

    for name, data in player_profiles.items():
        profile_listbox.insert(tk.END, f"{data['avatar']} {name} - Best: {data['high_score']}")

    def select_profile_action():
        selection = profile_listbox.curselection()
        if selection:
            selected_name = list(player_profiles.keys())[selection[0]]
            select_player(selected_name)
        else:
            messagebox.showwarning("Warning", "Please select a player.")

    def delete_profile_action():
        selection = profile_listbox.curselection()
        if selection:
            selected_name = list(player_profiles.keys())[selection[0]]
            if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{selected_name}'?"):
                del player_profiles[selected_name]
                save_data(PROFILES_FILE, player_profiles)
                messagebox.showinfo("Success", f"Profile '{selected_name}' deleted.")
                show_profile_selection() # Refresh list
        else:
            messagebox.showwarning("Warning", "Please select a player to delete.")

    button_frame = tk.Frame(root, bg="#1a1a2e")
    button_frame.pack(pady=10)
    create_ps1_button(button_frame, "SELECT", select_profile_action, width=15).pack(side='left', padx=5)
    create_ps1_button(button_frame, "DELETE", delete_profile_action, width=15).pack(side='left', padx=5)
    create_ps1_button(root, "BACK", show_main_menu).pack(pady=20)


def show_create_profile():
    for widget in root.winfo_children():
        widget.destroy()

    tk.Label(root, text="CREATE NEW PLAYER", font=("Courier New", 20, 'bold'), fg="#e94560", bg="#1a1a2e").pack(pady=20)

    input_frame = tk.Frame(root, bg="#16213e", relief='raised', bd=2)
    input_frame.pack(pady=10, padx=50, fill='x')

    tk.Label(input_frame, text="Name:", font=("Courier New", 12), fg="#f5f5f5", bg="#16213e").pack(pady=5)
    name_entry = tk.Entry(input_frame, font=("Courier New", 12), bg="#0f3460", fg="#f5f5f5", width=30)
    name_entry.pack(pady=5)

    tk.Label(input_frame, text="Avatar:", font=("Courier New", 12), fg="#f5f5f5", bg="#16213e").pack(pady=10)
    avatar_frame = tk.Frame(input_frame, bg="#16213e")
    avatar_frame.pack(pady=5)

    avatars = ["🎮", "🕹️", "👾", "🎯", "⭐", "🏆", "🎲", "🔥"]
    avatar_var = tk.StringVar(root, value=avatars[0])

    for i, avatar in enumerate(avatars):
        tk.Radiobutton(
            avatar_frame,
            text=avatar,
            variable=avatar_var,
            value=avatar,
            font=('Arial', 16),
            bg="#16213e",
            fg="#f5f5f5",
            selectcolor="#0f3460",
            activebackground="#16213e"
        ).grid(row=i//4, column=i%4, padx=5, pady=2)

    def create_profile_action():
        name = name_entry.get().strip()
        avatar = avatar_var.get()
        if name:
            if name in player_profiles:
                messagebox.showerror("Error", "Player name already exists.")
            else:
                player_profiles[name] = {"avatar": avatar, "high_score": 0}
                save_data(PROFILES_FILE, player_profiles)
                messagebox.showinfo("Success", f"Player '{name}' created successfully!")
                show_profile_selection()
        else:
            messagebox.showerror("Error", "Player name cannot be empty.")

    create_ps1_button(root, "CREATE", create_profile_action).pack(pady=20)
    create_ps1_button(root, "BACK", show_main_menu).pack(pady=10)


def select_player(name):
    global current_player, current_score
    current_player = name
    current_score = 0 # Reset score for new game session
    messagebox.showinfo("Player Selected", f"Welcome, {current_player}!")
    show_game_interface()

def show_game_interface():
    global seven_seg_display_label, excess3_output_label, excess3_valid_label, current_score_label, current_player_label
    for widget in root.winfo_children():
        widget.destroy()

    stop_music() # Stop menu music

    game_frame = tk.Frame(root, bg="#1a1a2e")
    game_frame.pack(fill='both', expand=True)

    tk.Label(game_frame, text="GAME IN PROGRESS", font=("Courier New", 24, 'bold'), fg="#e94560", bg="#1a1a2e").pack(pady=20)

    current_player_label = tk.Label(game_frame, text=f"Player: {current_player} {player_profiles[current_player]['avatar']}", font=("Courier New", 16), fg="#f5f5f5", bg="#1a1a2e")
    current_player_label.pack(pady=5)
    current_score_label = tk.Label(game_frame, text=f"Current Score: {current_score}", font=("Courier New", 16), fg="#f5f5f5", bg="#1a1a2e")
    current_score_label.pack(pady=5)

    # --- Display de 7 Segmentos ---
    tk.Label(game_frame, text="7-Segment Display Value:", font=("Courier New", 14), fg="#f5f5f5", bg="#1a1a2e").pack(pady=(20,5))
    seven_seg_display_label = tk.Label(game_frame, text="0", font=("Courier New", 48, 'bold'), fg="#00FF00", bg="#1a1a2e", relief='sunken', bd=3, width=2)
    seven_seg_display_label.pack(pady=5)

    # --- Salida del Circuito Exceso 3 ---
    tk.Label(game_frame, text="Excess-3 Circuit Output:", font=("Courier New", 14), fg="#f5f5f5", bg="#1a1a2e").pack(pady=(20,5))
    excess3_output_label = tk.Label(game_frame, text="----", font=("Courier New", 36, 'bold'), fg="#FFFF00", bg="#1a1a2e", relief='sunken', bd=3, width=4)
    excess3_output_label.pack(pady=5)

    # --- Bit de Validación ---
    tk.Label(game_frame, text="Validation Bit:", font=("Courier New", 14), fg="#f5f5f5", bg="#1a1a2e").pack(pady=(10,5))
    excess3_valid_label = tk.Label(game_frame, text="OFF", font=("Courier New", 24, 'bold'), fg="red", bg="#1a1a2e", relief='sunken', bd=3, width=4)
    excess3_valid_label.pack(pady=5)

    create_ps1_button(game_frame, "END GAME", end_game).pack(pady=30)

def update_game_display(seven_seg_val, excess3_out, valid_bit):
    global current_score
    # El puntaje actual del juego es el valor del 7-seg
    current_score = int(seven_seg_val, 16)

    if seven_seg_display_label:
        seven_seg_display_label.config(text=seven_seg_val)
    if current_score_label:
        current_score_label.config(text=f"Current Score: {current_score}")
    if excess3_output_label:
        excess3_output_label.config(text=excess3_out)
    if excess3_valid_label:
        if valid_bit == '1':
            excess3_valid_label.config(text="ON", fg="lime green")
        else:
            excess3_valid_label.config(text="OFF", fg="red")


def end_game():
    global current_player, current_score

    if current_player:
        # Update high score if necessary
        if current_score > player_profiles[current_player]['high_score']:
            player_profiles[current_player]['high_score'] = current_score
            save_data(PROFILES_FILE, player_profiles)
            messagebox.showinfo("New Record!", f"Congratulations, {current_player}! You set a new record: {current_score}")

        # Update rankings
        update_rankings(current_player, current_score)

        response = messagebox.askyesno("Game Over",
                                       f"Game for {current_player} ended. Final Score: {current_score}\n"
                                       "Do you want to play again with the same profile?")
        if response:
            current_score = 0 # Reset score for new game session
            show_game_interface()
        else:
            current_player = None
            current_score = 0
            show_main_menu()
    else:
        show_main_menu() # If no player selected, go back to main menu

def update_rankings(player_name, score):
    global game_rankings
    # Remove old entries for the same player to keep only the highest
    game_rankings = [r for r in game_rankings if r['name'] != player_name]
    game_rankings.append({'name': player_name, 'score': score})
    # Sort by score descending
    game_rankings.sort(key=lambda x: x['score'], reverse=True)
    # Keep only the top N (e.g., top 10)
    game_rankings = game_rankings[:10]
    save_data(RANKINGS_FILE, game_rankings)

def show_rankings():
    for widget in root.winfo_children():
        widget.destroy()

    tk.Label(root, text="HIGH SCORES", font=("Courier New", 20, 'bold'), fg="#e94560", bg="#1a1a2e").pack(pady=30)

    rankings_container = tk.Frame(root, bg="#16213e", relief='raised', bd=2)
    rankings_container.pack(padx=50, pady=20, fill='both', expand=True)

    headers_frame = tk.Frame(rankings_container, bg="#0f3460")
    headers_frame.pack(fill='x', padx=10, pady=10)

    tk.Label(headers_frame, text="RANK", font=('Courier New', 12, 'bold'), fg="#f5f5f5", bg="#0f3460", width=8).pack(side='left')
    tk.Label(headers_frame, text="PLAYER", font=('Courier New', 12, 'bold'), fg="#f5f5f5", bg="#0f3460", width=20).pack(side='left')
    tk.Label(headers_frame, text="SCORE", font=('Courier New', 12, 'bold'), fg="#f5f5f5", bg="#0f3460", width=10).pack(side='left')

    rankings_list_frame = tk.Frame(rankings_container, bg="#16213e")
    rankings_list_frame.pack(fill='both', expand=True, padx=10, pady=10)

    # Clear previous rankings
    for widget in rankings_list_frame.winfo_children():
        widget.destroy()

    for i, entry in enumerate(game_rankings):
        rank_frame = tk.Frame(rankings_list_frame, bg="#16213e")
        rank_frame.pack(fill='x', pady=2)

        rank_color = "#e94560" if i < 3 else "#f5f5f5"

        tk.Label(rank_frame, text=f"#{i+1}", font=('Courier New', 10), fg=rank_color, bg="#16213e", width=8).pack(side='left')
        tk.Label(rank_frame, text=f"{player_profiles.get(entry['name'], {}).get('avatar', '')} {entry['name']}", font=('Courier New', 10), fg="#f5f5f5", bg="#16213e", width=20).pack(side='left')
        tk.Label(rank_frame, text=str(entry['score']), font=('Courier New', 10), fg=rank_color, bg="#16213e", width=10).pack(side='left')

    create_ps1_button(root, "BACK", show_main_menu).pack(pady=20)

# --- Hilo para la Comunicación de Red ---
def network_thread_function():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Permite reutilizar la dirección
    server_socket.bind((HOST, PORT))
    server_socket.listen(1)
    print(f"Escuchando conexiones en {HOST}:{PORT}")

    while True:
        conn, addr = server_socket.accept()
        print(f"Conexión establecida desde {addr}")
        try:
            while True:
                data = conn.recv(1024).decode('utf-8')
                if not data:
                    break
                print(f"Recibido de Pico W: {data}")
                # Parsear el mensaje: "7SEG:X;EXCESS3:O3O2O1O0;VALID:V"
                parts = data.split(';')
                seven_seg_val = "c"
                excess3_out = "----"
                valid_bit = "0"

                for part in parts:
                    if part.startswith("7SEG:"):
                        seven_seg_val = part.split(":")[1]
                    elif part.startswith("EXCESS3:"):
                        excess3_out = part.split(":")[1]
                    elif part.startswith("VALID:"):
                        valid_bit = part.split(":")[1]

                # Actualizar la GUI en el hilo principal de Tkinter
                root.after(0, update_game_display, seven_seg_val, excess3_out, valid_bit)

        except Exception as e:
            print(f"Error en la comunicación con {addr}: {e}")
        finally:
            conn.close()
            print(f"Conexión con {addr} cerrada.")

# --- Inicialización de la Aplicación ---
if __name__ == "__main__":
    # Cargar datos al inicio
    player_profiles = load_data(PROFILES_FILE, {})
    game_rankings = load_data(RANKINGS_FILE, [])

    # Inicializar Pygame Mixer para la música
    pygame.mixer.init()

    root = tk.Tk()
    root.title("BUTTONS & LIGHTS")
    root.geometry("800x600")
    root.configure(bg='#1a1a2e') # Fondo oscuro estilo PS1
    root.resizable(False, False)

    # Iniciar el hilo de red
    network_thread = threading.Thread(target=network_thread_function, daemon=True)
    network_thread.start()

    show_main_menu() # Mostrar el menú principal al inicio

    root.mainloop()
