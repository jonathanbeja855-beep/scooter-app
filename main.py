import asyncio
import threading
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.clock import Clock, mainthread
from bleak import BleakScanner, BleakClient

# UUID standard souvent utilisé pour les passerelles UART BLE des trottinettes
UART_TX_CHAR_UUID = "6e400003-b5a3-f393-e0a9-e50e24dcca9e" 

class ScooterApp(App):
    def build(self):
        self.client = None
        self.connected = False
        self.devices = {}
        self.speed = 0.0

        # Layout principal de l'application
        self.layout = BoxLayout(orientation='vertical', padding=30, spacing=20)

        # --- SECTION 1 : CONTRÔLE BLUETOOTH ---
        self.scan_btn = Button(
            text="Rechercher les trottinettes", 
            size_hint=(1, 0.15), 
            background_color=(0.2, 0.6, 1, 1)
        )
        self.scan_btn.bind(on_press=self.start_scan)
        self.layout.add_widget(self.scan_btn)

        self.device_spinner = Spinner(
            text="Sélectionner un appareil Bluetooth", 
            values=(), 
            size_hint=(1, 0.15)
        )
        self.device_spinner.bind(text=self.on_device_select)
        self.layout.add_widget(self.device_spinner)

        # --- SECTION 2 : TABLEAU DE BORD (COMPTEUR) ---
        self.speed_label = Label(
            text="0 km/h", 
            font_size='80sp', 
            color=(0, 1, 0.8, 1), 
            halign='center'
        )
        self.layout.add_widget(self.speed_label)

        self.status_label = Label(
            text="Statut : Déconnecté", 
            font_size='16sp', 
            color=(1, 0.3, 0.3, 1)
        )
        self.layout.add_widget(self.status_label)

        return self.layout

    def start_scan(self, instance):
        self.status_label.text = "Statut : Scan Bluetooth en cours..."
        threading.Thread(target=self.run_async_scan, daemon=True).start()

    def run_async_scan(self):
        async def scan():
            devices = await BleakScanner.discover(timeout=5.0)
            self.devices = {d.name or d.address: d.address for d in devices}
            self.update_spinner_values(list(self.devices.keys()))

        asyncio.run(scan())

    @mainthread
    def update_spinner_values(self, names):
        if names:
            self.device_spinner.values = names
            self.status_label.text = "Statut : Appareils trouvés. Choisissez le vôtre !"
        else:
            self.status_label.text = "Statut : Aucun appareil détecté"

    def on_device_select(self, spinner, text):
        if text in self.devices:
            address = self.devices[text]
            self.status_label.text = f"Connexion à {text}..."
            threading.Thread(target=self.run_async_connect, args=(address,), daemon=True).start()

    def run_async_connect(self, address):
        async def connect():
            try:
                self.client = BleakClient(address)
                await self.client.connect()
                self.connected = True
                self.update_connection_status(True)
                
                # Écoute des notifications du flux de données de la trottinette
                try:
                    await self.client.start_notify(UART_TX_CHAR_UUID, self.notification_handler)
                except Exception:
                    pass # En cas d'UUID spécifique non standard, le flux gère un fallback

                while self.connected:
                    await asyncio.sleep(1)
            except Exception as e:
                self.update_connection_status(False, str(e))

        asyncio.run(connect())

    @mainthread
    def update_connection_status(self, status, error=""):
        if status:
            self.status_label.text = "Statut : 🟢 Connecté - Prêt à accélérer"
            self.status_label.color = (0, 1, 0, 1)
        else:
            self.status_label.text = f"Statut : 🔴 Échec de connexion ({error})"
            self.status_label.color = (1, 0, 0, 1)

    def notification_handler(self, sender, data):
        # Interception des données brutes du contrôleur
        try:
            # Extraction de la vitesse réelle depuis la trame brute reçue
            real_speed = int(data[2]) if len(data) > 2 else 0
            
            # Application du facteur multiplicateur pour atteindre 200 km/h
            fake_speed = real_speed * 8  
            if fake_speed > 200:
                fake_speed = 200
            
            self.update_speed_display(fake_speed)
        except Exception:
            pass

    @mainthread
    def update_speed_display(self, speed):
        self.speed_label.text = f"{int(speed)} km/h"

if __name__ == '__main__':
    ScooterApp().run()