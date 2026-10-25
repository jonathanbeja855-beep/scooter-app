[app]
title = Scooter Speed Hack
package.name = scooterspeed
package.domain = org.scooter
source.include_exts = py,png,jpg,kv,atlas
version = 0.1
requirements = python3,kivy,bleak,pyjnius
orientation = portrait
fullscreen = 0
android.permissions = INTERNET,BLUETOOTH,BLUETOOTH_ADMIN,BLUETOOTH_SCAN,BLUETOOTH_CONNECT,ACCESS_FINE_LOCATION
android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a

[buildozer]
log_level = 2
warn_on_root = 1