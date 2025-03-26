import time
import schedule
import requests
from flask import Flask, render_template, request, redirect, url_for
from flask_socketio import SocketIO, emit
import docker
import docker.errors
import paramiko
import threading
import socket
import os
import shutil

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Tijdelijke directory voor speler-broncode
PLAYER_SOURCE_DIR = "/tmp/player_source"

# Maak de directory en kopieer originele broncode als die nog niet bestaat
if not os.path.exists(PLAYER_SOURCE_DIR):
    os.makedirs(PLAYER_SOURCE_DIR)
    ORIGINAL_SOURCE_DIR = "./target"  # Waar je originele Dockerfile en bestanden staan
    shutil.copytree(ORIGINAL_SOURCE_DIR, PLAYER_SOURCE_DIR, dirs_exist_ok=True)

class Container:
    def __init__(self, name, port, ssh_port):
        self.name = name
        self.container = None
        self.ssh_client = None
        self.port = port
        self.ssh_port = ssh_port

    def wait_for_ssh(self):
        for attempt in range(15):
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(1)
                socketio.emit(f"{self.name}_output", {'data': f"Probeer SSH-verbinding (poging {attempt + 1}) op 127.0.0.1:{self.ssh_port}"})
                s.connect(('127.0.0.1', self.ssh_port))
                s.close()
                socketio.emit(f"{self.name}_output", {'data': f"SSH bereikbaar op 127.0.0.1:{self.ssh_port}"})
                return True
            except Exception as e:
                socketio.emit(f"{self.name}_output", {'data': f"SSH nog niet bereikbaar: {e}"})
                time.sleep(1)
        socketio.emit(f"{self.name}_output", {'data': f"SSH niet bereikbaar na 15 pogingen"})
        return False

    def start(self, docker_client):
        try:
            try:
                existing_container = docker_client.containers.get(f"cyber-game-{self.name}")
                socketio.emit(f"{self.name}_output", {'data': f"Bestaande {self.name}-container gevonden: {existing_container.id}. Wordt verwijderd..."})
                existing_container.stop()
                existing_container.remove()
            except docker.errors.NotFound:
                pass

            if not self.container:
                socketio.emit(f"{self.name}_output", {'data': f"Starten van {self.name}-container..."})
                self.container = docker_client.containers.run(
                    'cyber-game-target',
                    name=f"cyber-game-{self.name}",
                    detach=True,
                    ports={'5001/tcp': self.port, '22/tcp': self.ssh_port}
                )
                if self.wait_for_ssh():
                    self.setup_ssh()
                    if self.ssh_client:
                        socketio.emit(f"{self.name}_output", {'data': f"{self.name.capitalize()}-container gestart: {self.container.id}"})
                    else:
                        raise Exception("SSH-verbinding kon niet worden opgezet")
                else:
                    raise Exception("SSH niet bereikbaar na starten container")
        except Exception as e:
            socketio.emit(f"{self.name}_output", {'data': f"Fout bij starten {self.name}-container: {e}"})
            if self.container:
                self.container.stop()
                self.container.remove()
                self.container = None

    def setup_ssh(self):
        attempts = 3
        for attempt in range(attempts):
            try:
                if not self.ssh_client:
                    socketio.emit(f"{self.name}_output", {'data': f"Probeer SSH-verbinding op te zetten (poging {attempt + 1})"})
                    self.ssh_client = paramiko.SSHClient()
                    self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    self.ssh_client.connect('127.0.0.1', port=self.ssh_port, username='root', password='secret', timeout=10)
                    socketio.emit(f"{self.name}_output", {'data': f"{self.name.capitalize()} SSH-verbinding opgezet"})
                    return
            except Exception as e:
                self.ssh_client = None
                socketio.emit(f"{self.name}_output", {'data': f"Fout bij opzetten SSH voor {self.name} (poging {attempt + 1}): {e}"})
                if attempt < attempts - 1:
                    time.sleep(2)
                else:
                    socketio.emit(f"{self.name}_output", {'data': f"SSH-verbinding mislukt na {attempts} pogingen"})

    def stop(self):
        try:
            if self.container:
                socketio.emit(f"{self.name}_output", {'data': f"Stoppen van {self.name}-container: {self.container.id}"})
                self.container.stop()
                self.container.remove()
                self.container = None
                if self.ssh_client:
                    self.ssh_client.close()
                    self.ssh_client = None
        except Exception as e:
            socketio.emit(f"{self.name}_output", {'data': f"Fout bij stoppen {self.name}-container: {e}"})

    def rebuild(self, docker_client):
            self.stop()
            socketio.emit(f"{self.name}_output", {'data': f"Rebuilding {self.name} container..."})
            try:
                # Bouw een nieuwe image met de aangepaste broncode
                socketio.emit(f"{self.name}_output", {'data': "Building new Docker image..."})
                docker_client.images.build(
                    path=PLAYER_SOURCE_DIR,
                    tag="cyber-game-target",
                    rm=True,
                )
                socketio.emit(f"{self.name}_output", {'data': "Docker image succesvol gebouwd."})
                self.start(docker_client)
                socketio.emit(f"{self.name}_output", {'data': f"{self.name.capitalize()} container herbouwd en gestart"})
            except Exception as e:
                socketio.emit(f"{self.name}_output", {'data': f"Fout bij rebuild {self.name}-container: {str(e)}"})
                # Start de oude container terug als fallback
                self.start(docker_client)

    def get_current_flag(self):
        if not self.ssh_client:
            socketio.emit(f"{self.name}_output", {'data': f"Geen SSH-verbinding beschikbaar voor {self.name}"})
            return None
        try:
            stdin, stdout, stderr = self.ssh_client.exec_command('sqlite3 /app/users.db "SELECT flag FROM flags WHERE id=1"')
            flag = stdout.read().decode('utf-8').strip()
            return flag if flag else None
        except Exception as e:
            socketio.emit(f"{self.name}_output", {'data': f"Fout bij ophalen flag voor {self.name}: {e}"})
            return None

    def is_running(self, docker_client):
        try:
            container = docker_client.containers.get(f"cyber-game-{self.name}")
            return container.status == 'running'
        except docker.errors.NotFound:
            return False

class GameState:
    def __init__(self):
        self.scores = {'player': 0, 'ai': 0}
        self.game_running = False

    def update_score(self, target, points):
        self.scores[target] += points
        socketio.emit('status', {'scores': self.scores})

    def reset(self):
        self.scores = {'player': 0, 'ai': 0}
        self.game_running = False

class GameManager:
    def __init__(self):
        self.player_container = Container('player', 5001, 2222)
        self.ai_container = Container('ai', 5002, 2223)
        self.state = GameState()
        try:
            self.docker_client = docker.DockerClient(base_url='unix://var/run/docker.sock')
            socketio.emit('player_output', {'data': 'Docker-client succesvol geïnitialiseerd'})
            socketio.emit('ai_output', {'data': 'Docker-client succesvol geïnitialiseerd'})
        except Exception as e:
            socketio.emit('player_output', {'data': f"Fout bij initialiseren Docker-client: {e}"})
            socketio.emit('ai_output', {'data': f"Fout bij initialiseren Docker-client: {e}"})
        self.current_exploit = None

    def start_game(self):
        if not self.state.game_running:
            self.player_container.start(self.docker_client)
            self.ai_container.start(self.docker_client)
            self.state.game_running = True
            socketio.emit('game_output', {'data': 'Spel gestart!'})
            self.update_status()

    def stop_game(self):
        if self.state.game_running:
            self.player_container.stop()
            self.ai_container.stop()
            self.state.reset()
            socketio.emit('game_output', {'data': 'Spel gestopt!'})
            self.update_status()

    def update_flags(self):
        try:
            requests.post('http://localhost:5001/set_flag')
            requests.post('http://localhost:5002/set_flag')
        except:
            pass

    def health_check(self):
        try:
            player_health = requests.get('http://localhost:5001/health').text == "OK"
            ai_health = requests.get('http://localhost:5002/health').text == "OK"
            if not player_health:
                self.state.update_score('player', -10)
            else:
                self.state.update_score('player', 5)
            if not ai_health:
                self.state.update_score('ai', -10)
            else:
                self.state.update_score('ai', 5)
        except:
            self.state.update_score('player', -10)
            self.state.update_score('ai', -10)
        self.update_status()

    def perform_exploit(self):
        if not self.state.game_running:
            return
        exploits = [
            {"username": "' OR 1=1 --", "password": "anything"},
            {"username": "admin", "password": "password123"},
        ]
        exploit = self.current_exploit if self.current_exploit else exploits[0]
        try:
            response = requests.post('http://localhost:5001/login', data=exploit, timeout=5)
            if "Login succesvol" in response.text:
                flag_response = requests.get('http://localhost:5001/get_flag', cookies=response.cookies)
                if flag_response.status_code == 200:
                    submitted_flag = flag_response.text
                    current_flag = self.player_container.get_current_flag()
                    if submitted_flag == current_flag:
                        if not self.current_exploit:
                            self.current_exploit = exploit
                        self.state.update_score('ai', 50)
                        socketio.emit('game_output', {'data': f"AI heeft jouw flag gestolen met payload {exploit}! AI scoort 50 punten. Flag: {submitted_flag}"})
                        self.update_flags()
                        return
            else:
                socketio.emit('game_output', {'data': f"AI payload {exploit} mislukt."})
                if self.current_exploit == exploit:
                    self.current_exploit = None
                    for new_exploit in exploits[1:]:
                        self.perform_exploit()
                        break
        except:
            socketio.emit('game_output', {'data': f"AI payload {exploit} veroorzaakte een fout."})

    def update_status(self):
        player_running = self.player_container.is_running(self.docker_client)
        ai_running = self.ai_container.is_running(self.docker_client)
        socketio.emit('game_output', {'data': f"Status update - Player: {player_running}, AI: {ai_running}"})
        socketio.emit('status', {
            'player_running': player_running,
            'ai_running': ai_running,
            'scores': self.state.scores
        })

game_manager = GameManager()

def run_game_loop():
    schedule.every(5).minutes.do(game_manager.update_flags)
    schedule.every(1).minute.do(game_manager.health_check)
    schedule.every(2).minutes.do(game_manager.perform_exploit)
    schedule.every(5).seconds.do(game_manager.update_status)
    while True:
        schedule.run_pending()
        time.sleep(1)

@socketio.on('connect')
def handle_connect(auth=None):
    socketio.emit('game_output', {'data': f"Welkom bij de Cyber Attack & Defend!\nGebruik een SSH-client om te verbinden."})
    game_manager.update_status()

@socketio.on('control')
def handle_control(data):
    action = data['action']
    target = data.get('target')
    if action == 'start':
        container = game_manager.player_container if target == 'player' else game_manager.ai_container
        container.start(game_manager.docker_client)
        socketio.emit('game_output', {'data': f"{target.capitalize()} container gestart."})
    elif action == 'stop':
        container = game_manager.player_container if target == 'player' else game_manager.ai_container
        container.stop()
        socketio.emit('game_output', {'data': f"{target.capitalize()} container gestopt."})
    elif action == 'rebuild':
        container = game_manager.player_container if target == 'player' else game_manager.ai_container
        container.rebuild(game_manager.docker_client)
        socketio.emit('game_output', {'data': f"{target.capitalize()} container herbouwd."})
    elif action == 'start_game':
        game_manager.start_game()
    elif action == 'stop_game':
        game_manager.stop_game()

@socketio.on('submit_flag')
def handle_submit_flag(data):
    flag = data['flag']
    target = data['target']
    current_flag = (game_manager.player_container if target == 'player' else game_manager.ai_container).get_current_flag()
    if current_flag and flag == current_flag:
        if target == 'ai':
            game_manager.state.update_score('player', 50)
            socketio.emit('game_output', {'data': f"Flag correct! Speler scoort 50 punten. Nieuwe scores: Speler: {game_manager.state.scores['player']}, AI: {game_manager.state.scores['ai']}"})
        elif target == 'player':
            game_manager.state.update_score('ai', 50)
            socketio.emit('game_output', {'data': f"AI heeft jouw flag gestolen! AI scoort 50 punten. Nieuwe scores: Speler: {game_manager.state.scores['player']}, AI: {game_manager.state.scores['ai']}"})
        game_manager.update_flags()
    else:
        socketio.emit('game_output', {'data': f"Verkeerde flag! (Huidige {target} flag was: {current_flag})"})
    game_manager.update_status()

@app.route('/editor', methods=['GET', 'POST'])
def editor():
    # Haal bestandenlijst op uit de tijdelijke broncode directory
    files = [f for f in os.listdir(PLAYER_SOURCE_DIR) if os.path.isfile(os.path.join(PLAYER_SOURCE_DIR, f))]
    selected_file = request.args.get('file', 'app.py')

    if request.method == 'POST':
        new_code = request.form.get('code')
        file_to_edit = request.form.get('file', selected_file)
        if file_to_edit in files:
            # Sla de wijzigingen op in de tijdelijke directory
            file_path = os.path.join(PLAYER_SOURCE_DIR, file_to_edit)
            with open(file_path, 'w') as f:
                f.write(new_code)
            socketio.emit('game_output', {'data': f"Bestand {file_to_edit} opgeslagen in broncode. Klik 'Rebuild' om de container te updaten."})
            return redirect(url_for('editor', file=file_to_edit))

    # Lees de inhoud van het geselecteerde bestand
    file_path = os.path.join(PLAYER_SOURCE_DIR, selected_file)
    code = ""
    if os.path.isfile(file_path):
        with open(file_path, 'r') as f:
            code = f.read()
    else:
        socketio.emit('game_output', {'data': f"Bestand {selected_file} niet gevonden in broncode."})

    return render_template('editor.html', files=files, selected_file=selected_file, code=code)

@app.route('/')
def index():
    return render_template('game.html')

if __name__ == '__main__':
    socketio.start_background_task(run_game_loop)
    socketio.run(app, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)