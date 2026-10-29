import asyncio
import threading
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.clock import Clock, mainthread
from kivy.logger import Logger
from bleak import BleakScanner, BleakClient

try:
    from android.permissions import request_permissions, Permission, check_permission
    from android import mActivity
    from jnius import autoclass
    ANDROID = True
except ImportError:
    ANDROID = False

# UUID Nordic UART (souvent utilisé par les trottinettes KuKirin / Xiaomi-like)
UART_SERVICE_UUID = "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
UART_TX_CHAR_UUID = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"  # Notify
UART_RX_CHAR_UUID = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"  # Write

class ScooterApp(App):
    def build(self):
        self.client = None
        self.connected = False
        self.devices = {}          # name -> address
        self.scanning = False

        self.layout = BoxLayout(orientation='vertical', padding=20, spacing=15)

        self.scan_btn = Button(
            text="Rechercher les trottinettes",
            size_hint=(1, 0.12),
            background_color=(0.2, 0.6, 1, 1)
        )
        self.scan_btn.bind(on_press=self.start_scan)
        self.layout.add_widget(self.scan_btn)

        self.device_spinner = Spinner(
            text="Sélectionner un appareil Bluetooth",
            values=(),
            size_hint=(1, 0.12)
        )
        self.device_spinner.bind(text=self.on_device_select)
        self.layout.add_widget(self.device_spinner)

        self.speed_label = Label(
            text="0 km/h",
            font_size='70sp',
            color=(0, 1, 0.8, 1),
            size_hint=(1, 0.35)
        )
        self.layout.add_widget(self.speed_label)

        self.status_label = Label(
            text="Statut : En attente des permissions...",
            font_size='15sp',
            color=(1, 0.4, 0.3, 1),
            size_hint=(1, 0.15)
        )
        self.layout.add_widget(self.status_label)

        # Demande des permissions dès le démarrage
        if ANDROID:
            Clock.schedule_once(lambda dt: self.ask_permissions(), 0.5)

        return self.layout

    def ask_permissions(self):
        perms = [
            Permission.BLUETOOTH_SCAN,
            Permission.BLUETOOTH_CONNECT,
            Permission.ACCESS_FINE_LOCATION,
            Permission.ACCESS_COARSE_LOCATION,
        ]
        request_permissions(perms, self.on_permissions_result)

    def on_permissions_result(self, permissions, grants):
        if all(grants):
            self.update_status("Permissions OK – activez aussi la Localisation (GPS) dans les réglages")
            # Vérifie si le service localisation est activé (très important sur Oppo)
            self.check_location_enabled()
        else:
            self.update_status("Permissions refusées ! Allez dans Réglages → Applications → Permissions")

    def check_location_enabled(self):
        if not ANDROID:
            return
        try:
            Context = autoclass('android.content.Context')
            LocationManager = autoclass('android.location.LocationManager')
            lm = mActivity.getSystemService(Context.LOCATION_SERVICE)
            gps = lm.isProviderEnabled(LocationManager.GPS_PROVIDER)
            net = lm.isProviderEnabled(LocationManager.NETWORK_PROVIDER)
            if not (gps or net):
                self.update_status("⚠️ ACTIVEZ LA LOCALISATION (GPS) dans les réglages système !")
            else:
                self.update_status("Prêt – Localisation OK")
        except Exception as e:
            Logger.warning(f"Location check failed: {e}")

    @mainthread
    def update_status(self, text):
        self.status_label.text = f"Statut : {text}"

    def start_scan(self, instance):
        if self.scanning:
            return
        self.scanning = True
        self.scan_btn.disabled = True
        self.update_status("Scan BLE en cours (10 s)...")
        self.device_spinner.values = ()
        self.devices.clear()

        threading.Thread(target=self.run_scan, daemon=True).start()

    def run_scan(self):
        async def do_scan():
            try:
                # Timeout plus long + retour des advertisement data
                devices = await BleakScanner.discover(
                    timeout=10.0,
                    return_adv=False
                )
                found = {}
                for d in devices:
                    name = d.name or "Inconnu"
                    # On garde aussi les appareils sans nom (beaucoup de trottinettes)
                    key = f"{name} [{d.address[-5:]}]"
                    found[key] = d.address
                    Logger.info(f"Trouvé : {key}")

                self.devices = found
                self.update_spinner(list(found.keys()))
            except Exception as e:
                Logger.error(f"Scan error: {e}")
                self.update_status(f"Erreur scan : {e}")
            finally:
                self.scanning = False
                Clock.schedule_once(lambda dt: setattr(self.scan_btn, 'disabled', False), 0)

        asyncio.run(do_scan())

    @mainthread
    def update_spinner(self, names):
        if names:
            self.device_spinner.values = names
            self.update_status(f"{len(names)} appareil(s) trouvé(s)")
        else:
            self.update_status("Aucun appareil – vérifiez Localisation ON + Bluetooth ON + permissions")

    def on_device_select(self, spinner, text):
        if text not in self.devices or self.connected:
            return
        address = self.devices[text]
        self.update_status(f"Connexion à {text}...")
        threading.Thread(target=self.run_connect, args=(address,), daemon=True).start()

    def run_connect(self, address):
        async def do_connect():
            try:
                self.client = BleakClient(address)
                await self.client.connect(timeout=15.0)
                self.connected = True
                self.update_status("🟢 Connecté")

                # Active les notifications
                try:
                    await self.client.start_notify(UART_TX_CHAR_UUID, self.notification_handler)
                except Exception as e:
                    Logger.warning(f"Notify failed: {e}")

                while self.connected and self.client.is_connected:
                    await asyncio.sleep(1.0)

            except Exception as e:
                self.connected = False
                self.update_status(f"🔴 Erreur : {e}")
            finally:
                if self.client and self.client.is_connected:
                    await self.client.disconnect()

        asyncio.run(do_connect())

    def notification_handler(self, sender, data: bytearray):
        try:
            # Exemple de parsing (à adapter selon le protocole réel de ta G2)
            if len(data) >= 3:
                real_speed = data[2]          # souvent le 3e octet
                fake_speed = min(real_speed * 8, 99)
                self.update_speed(fake_speed)
        except Exception:
            pass

    @mainthread
    def update_speed(self, speed):
        self.speed_label.text = f"{int(speed)} km/h"

    def on_stop(self):
        self.connected = False
        if self.client:
            try:
                asyncio.run(self.client.disconnect())
            except Exception:
                pass

if __name__ == '__main__':
    ScooterApp().run()
