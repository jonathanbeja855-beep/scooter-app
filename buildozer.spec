[app]
source.dir = .
title = Scooter Speed Hack
package.name = scooterspeed
package.domain = org.scooter
source.include_exts = py,png,jpg,kv,atlas
version = 0.2

# Force la même version pour hostpython3 et python3
requirements = hostpython3==3.11.10,python3==3.11.10,kivy==2.3.0,bleak,pyjnius,android,async-timeout,pillow

orientation = portrait
fullscreen = 0

android.permissions = INTERNET,BLUETOOTH,BLUETOOTH_ADMIN,BLUETOOTH_SCAN,BLUETOOTH_CONNECT,ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION

android.api = 33
android.minapi = 24
android.ndk = 25b
android.archs = arm64-v8a
android.accept_sdk_license = True

p4a.branch = master

[buildozer]
log_level = 2
warn_on_root = 0
