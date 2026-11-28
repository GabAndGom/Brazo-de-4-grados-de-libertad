import sys, gi
gi.require_version('Gtk', '3.0')
try: gi.require_version('WebKit2', '4.1')
except ValueError: gi.require_version('WebKit2', '4.0')
from gi.repository import Gtk, WebKit2, GLib
url, salida, w, h, espera = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), float(sys.argv[5])
js = sys.argv[6] if len(sys.argv) > 6 else ''
win = Gtk.OffscreenWindow(); win.set_default_size(w, h)
wv = WebKit2.WebView(); s = wv.get_settings(); s.set_enable_webgl(True); s.set_hardware_acceleration_policy(WebKit2.HardwareAccelerationPolicy.ALWAYS)
wv.set_size_request(w, h); win.add(wv); win.show_all()
def listo(*a):
    surf = wv.get_snapshot_finish(a[1]); surf.write_to_png(salida); Gtk.main_quit()
def tomar():
    wv.get_snapshot(WebKit2.SnapshotRegion.VISIBLE, WebKit2.SnapshotOptions.NONE, None, listo); return False
def correr_js():
    if js: wv.run_javascript(js, None, None, None)
    GLib.timeout_add(int(espera*1000), tomar); return False
wv.connect('load-changed', lambda v, e: e == WebKit2.LoadEvent.FINISHED and GLib.timeout_add(2500, correr_js))
wv.load_uri(url); GLib.timeout_add(60000, Gtk.main_quit); Gtk.main()
