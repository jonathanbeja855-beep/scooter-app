[app]
source.dir = .
title = Scooter Speed Hack
package.name = scooterspeed
package.domain = org.scooter
source.include_exts = py,png,jpg,kv,atlas
version = 0.5

requirements = hostpython3==3.10.14,python3==3.10.14,kivy==2.2.1,bleak==0.22.3,pyjnius,android,async-timeout,pillow,typing_extensions

orientation = portrait
fullscreen = 0

android.permissions = INTERNET,BLUETOOTH,BLUETOOTH_ADMIN,BLUETOOTH_SCAN,BLUETOOTH_CONNECT,ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION

android.api = 33
android.minapi = 24
android.ndk = 25b
android.archs = arm64-v8a
android.accept_sdk_license = True

# Force l’utilisation de la recette officielle de Bleak qui contient les Java
p4a.local_recipes = 
p4a.branch = master

[buildozer]
log_level = 2
warn_on_root = 0
