import traceback
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock

class DebugApp(App):
    def build(self):
        self.root = BoxLayout(orientation='vertical', padding=20)

        self.label = Label(
            text="Démarrage...\n",
            size_hint_y=None,
            text_size=(None, None),
            halign='left',
            valign='top'
        )
        self.label.bind(texture_size=self._update_height)

        scroll = ScrollView()
        scroll.add_widget(self.label)
        self.root.add_widget(scroll)

        Clock.schedule_once(self.start_test, 0.5)
        return self.root

    def _update_height(self, instance, size):
        instance.height = size[1]
        instance.text_size = (self.root.width - 40, None)

    def log(self, msg):
        print(msg)
        self.label.text += msg + "\n"

    def start_test(self, dt):
        try:
            self.log("1. Import kivy OK")

            # Test Android
            try:
                from android.permissions import request_permissions, Permission
                self.log("2. android.permissions OK")
                ANDROID = True
            except Exception as e:
                self.log(f"2. android.permissions ÉCHEC : {e}")
                ANDROID = False

            # Test bleak
            try:
                from bleak import BleakScanner
                self.log("3. bleak import OK")
            except Exception as e:
                self.log(f"3. bleak import ÉCHEC : {e}")
                self.log(traceback.format_exc())
                return

            # Test permissions
            if ANDROID:
                try:
                    request_permissions([
                        Permission.BLUETOOTH_SCAN,
                        Permission.BLUETOOTH_CONNECT,
                        Permission.ACCESS_FINE_LOCATION
                    ])
                    self.log("4. request_permissions appelé")
                except Exception as e:
                    self.log(f"4. request_permissions ÉCHEC : {e}")

            self.log("\n=== Tout semble OK ===")
            self.log("L'application devrait normalement fonctionner.")
            self.log("Si ça crash encore, le problème est ailleurs.")

        except Exception as e:
            self.log("\n===== CRASH =====")
            self.log(str(e))
            self.log(traceback.format_exc())

if __name__ == '__main__':
    DebugApp().run()
