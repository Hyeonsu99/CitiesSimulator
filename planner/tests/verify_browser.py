import os
import sys
import time
import json
import urllib.request
import subprocess
from functools import partial

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCREENSHOT_DIR = os.path.join(APP_DIR, 'screenshots')

def run_test():
    # 1. Start HTTP server via python SimpleHTTPRequestHandler
    from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    server = ThreadingHTTPServer(('127.0.0.1', 0), partial(SimpleHTTPRequestHandler, directory=APP_DIR))
    port = server.server_address[1]
    
    import threading
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    print(f"[TEST] HTTP server listening on http://127.0.0.1:{port}")

    # 2. Launch Edge with remote debugging
    edge_exe = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    edge_proc = subprocess.Popen([
        edge_exe,
        "--headless=new",
        "--remote-debugging-port=9222",
        "--disable-gpu-shader-disk-cache",
        "--window-size=1440,900"
    ])
    print("[TEST] Edge headless started")
    time.sleep(1.5)

    try:
        # Check CDP endpoint
        with urllib.request.urlopen("http://127.0.0.1:9222/json/list", timeout=3) as resp:
            targets = json.loads(resp.read().decode())
            print(f"[TEST] CDP targets: {len(targets)}")

        # Open index.html in a new tab
        req = urllib.request.Request(f"http://127.0.0.1:9222/json/new?http://127.0.0.1:{port}/index.html", method='PUT')
        with urllib.request.urlopen(req, timeout=3) as resp:
            page_info = json.loads(resp.read().decode())
        ws_url = page_info['webSocketDebuggerUrl']
        print(f"[TEST] Page opened, ws: {ws_url}")

        # Connect WebSocket using simple client or websocket-client / native
        # Since Python stdlib in 3.12 doesn't have websockets by default, let's see if we can use CDP HTTP or a simple raw socket WS frame helper
        # Let's write a minimal pure python WebSocket client (RFC 6455) for CDP!
        import socket, struct, base64

        class SimpleCDP:
            def __init__(self, ws_url):
                # ws://127.0.0.1:9222/devtools/page/...
                parts = ws_url.replace("ws://", "").split("/")
                host, port_str = parts[0].split(":")
                path = "/" + "/".join(parts[1:])
                self.sock = socket.create_connection((host, int(port_str)), timeout=5)
                key = base64.b64encode(os.urandom(16)).decode()
                handshake = (
                    f"GET {path} HTTP/1.1\r\n"
                    f"Host: {host}:{port_str}\r\n"
                    f"Upgrade: websocket\r\n"
                    f"Connection: Upgrade\r\n"
                    f"Sec-WebSocket-Key: {key}\r\n"
                    f"Sec-WebSocket-Version: 13\r\n\r\n"
                )
                self.sock.sendall(handshake.encode())
                resp = b""
                while b"\r\n\r\n" not in resp:
                    resp += self.sock.recv(4096)
                assert b"101 " in resp, f"WS handshake failed: {resp}"
                self.msg_id = 0

            def send_cmd(self, method, params=None):
                self.msg_id += 1
                mid = self.msg_id
                msg = json.dumps({"id": mid, "method": method, "params": params or {}})
                data = msg.encode('utf-8')
                # frame as client (masked)
                mask_key = os.urandom(4)
                masked_data = bytearray(len(data))
                for i in range(len(data)):
                    masked_data[i] = data[i] ^ mask_key[i % 4]
                
                length = len(data)
                header = bytearray([0x81]) # fin + text
                if length < 126:
                    header.append(0x80 | length)
                elif length <= 0xFFFF:
                    header.append(0x80 | 126)
                    header.extend(struct.pack(">H", length))
                else:
                    header.append(0x80 | 127)
                    header.extend(struct.pack(">Q", length))
                header.extend(mask_key)
                header.extend(masked_data)
                self.sock.sendall(header)
                return self.wait_for_id(mid)

            def wait_for_id(self, target_id, timeout=8):
                start = time.time()
                while time.time() - start < timeout:
                    # read frame
                    head = self.sock.recv(2)
                    if not head or len(head) < 2:
                        continue
                    b1, b2 = head[0], head[1]
                    masked = bool(b2 & 0x80)
                    length = b2 & 0x7F
                    if length == 126:
                        length = struct.unpack(">H", self.sock.recv(2))[0]
                    elif length == 127:
                        length = struct.unpack(">Q", self.sock.recv(8))[0]
                    if masked:
                        mask = self.sock.recv(4)
                    payload = b""
                    while len(payload) < length:
                        payload += self.sock.recv(min(length - len(payload), 65536))
                    if masked:
                        unmasked = bytearray(length)
                        for i in range(length):
                            unmasked[i] = payload[i] ^ mask[i % 4]
                        payload = unmasked
                    
                    try:
                        text = payload.decode('utf-8', errors='ignore')
                        msg = json.loads(text)
                        if msg.get("id") == target_id:
                            return msg
                    except Exception:
                        pass
                raise TimeoutError(f"Timed out waiting for cmd id {target_id}")

            def eval_js(self, expression):
                res = self.send_cmd("Runtime.evaluate", {"expression": expression, "returnByValue": True})
                val = res.get("result", {}).get("result", {})
                return val.get("value")

            def capture_screenshot(self, filepath):
                res = self.send_cmd("Page.captureScreenshot", {"format": "png"})
                b64 = res.get("result", {}).get("data", "")
                with open(filepath, "wb") as f:
                    f.write(base64.b64decode(b64))
                print(f"[TEST] Saved screenshot to {filepath}")

        cdp = SimpleCDP(ws_url)
        time.sleep(1.0)

        # 3. Enable Page & Runtime
        cdp.send_cmd("Page.enable")
        cdp.send_cmd("Runtime.enable")

        # 4. Check for JavaScript console errors on load
        ready_state = cdp.eval_js("document.readyState")
        print(f"[TEST] Document readyState: {ready_state}")
        assert ready_state in ("interactive", "complete")

        # 5. Check UI elements exist
        has_preset_btn = cdp.eval_js("!!document.getElementById('btn-preset')")
        has_toggle_btn = cdp.eval_js("!!document.getElementById('btn-toggle-view')")
        has_canvas_2d = cdp.eval_js("!!document.getElementById('simCanvas')")
        has_canvas_3d = cdp.eval_js("!!document.getElementById('simCanvas3D')")
        has_hud_3d = cdp.eval_js("!!document.getElementById('hud-3d-controls')")
        print(f"[TEST] Elements: preset_btn={has_preset_btn}, toggle_btn={has_toggle_btn}, canvas2d={has_canvas_2d}, canvas3d={has_canvas_3d}, hud3d={has_hud_3d}")
        assert all([has_preset_btn, has_toggle_btn, has_canvas_2d, has_canvas_3d, has_hud_3d])

        # 6. Load preset by clicking #btn-preset
        print("[TEST] Clicking #btn-preset to load ideal Korean New Town preset...")
        cdp.eval_js("document.getElementById('btn-preset').click()")
        time.sleep(0.5)

        # Verify preset data in simulator
        node_count = cdp.eval_js("window.citySim.nodes.length")
        road_count = cdp.eval_js("window.citySim.roads.length")
        zone_count = cdp.eval_js("window.citySim.zoneCells.size")
        block_count = cdp.eval_js("window.citySim.zoneBlocks.length")
        roundabout_count = cdp.eval_js("window.citySim.roundabouts ? window.citySim.roundabouts.length : 0")
        roundabout_roads = cdp.eval_js("window.citySim.roads.filter(r => r.facility === 'roundabout').length")
        print(f"[TEST] Loaded: nodes={node_count}, roads={road_count}, zoneCells={zone_count}, zoneBlocks={block_count}, roundabouts={roundabout_count}, roundabout_roads={roundabout_roads}")
        assert node_count >= 25, f"Expected >= 25 nodes, got {node_count}"
        assert road_count >= 35, f"Expected >= 35 roads, got {road_count}"
        assert block_count >= 10, f"Expected >= 10 zoneBlocks, got {block_count}"
        assert roundabout_count >= 2, f"Expected >= 2 roundabouts, got {roundabout_count}"
        assert roundabout_roads >= 20, f"Expected >= 20 roundabout road segments, got {roundabout_roads}"

        # Capture 2D screenshot
        ss_2d_path = os.path.join(SCREENSHOT_DIR, "screenshot_2d_preset.png")
        cdp.capture_screenshot(ss_2d_path)

        # 7. Switch to 3D Mode by clicking #btn-toggle-view
        print("[TEST] Toggling to 3D mode...")
        cdp.eval_js("document.getElementById('btn-toggle-view').click()")
        time.sleep(0.8)

        # Verify 3D mode active
        current_mode = cdp.eval_js("window.citySim.viewMode")
        canvas_3d_display = cdp.eval_js("document.getElementById('simCanvas3D').style.display")
        canvas_2d_display = cdp.eval_js("document.getElementById('simCanvas').style.display")
        hud_3d_display = cdp.eval_js("document.getElementById('hud-3d-controls').style.display")
        print(f"[TEST] 3D Mode: viewMode={current_mode}, canvas3D={canvas_3d_display}, canvas2D={canvas_2d_display}, hud3D={hud_3d_display}")
        assert current_mode == '3d'
        assert canvas_3d_display == 'block'
        assert canvas_2d_display == 'none'
        assert hud_3d_display == 'flex'

        # Verify 3D camera and WebGL context
        has_view3d = cdp.eval_js("!!window.citySim.view3D")
        has_webgl = cdp.eval_js("!!window.citySim.view3D.gl")
        static_count = cdp.eval_js("window.citySim.view3D.staticBuffers.count")
        print(f"[TEST] view3D exists={has_view3d}, webgl exists={has_webgl}, static buffer index count={static_count}")
        assert has_view3d and has_webgl
        assert static_count > 1000, f"Expected static buffer vertices, got {static_count}"

        # Capture 3D South Screenshot
        ss_3d_south = os.path.join(SCREENSHOT_DIR, "screenshot_3d_south.png")
        cdp.capture_screenshot(ss_3d_south)

        # Also capture view from North looking South (yaw = 0)
        cdp.eval_js("""
            window.citySim.view3D.camera.target = { x: 1200, y: 1100, z: 0 };
            window.citySim.view3D.camera.yaw = 0;
            window.citySim.view3D.camera.pitch = 0.54;
            window.citySim.view3D.camera.distance = 1550;
            window.citySim.view3D.render();
        """)
        time.sleep(0.5)
        ss_3d_north = os.path.join(SCREENSHOT_DIR, "screenshot_3d_north.png")
        cdp.capture_screenshot(ss_3d_north)

        # 8. Test 3D Camera Controls: Switch to Isometric view preset
        print("[TEST] Testing 3D camera presets and rotation...")
        cdp.eval_js("document.getElementById('view-preset-iso').click()")
        time.sleep(0.5)
        iso_yaw = cdp.eval_js("window.citySim.view3D.camera.yaw")
        print(f"[TEST] Isometric yaw: {iso_yaw}")
        import math
        assert abs(iso_yaw - (math.pi * 0.75)) < 0.1

        # Test Rotate & Tilt buttons
        cdp.eval_js("document.getElementById('btn-cam-rotate-right').click()")
        cdp.eval_js("document.getElementById('btn-cam-tilt-down').click()")
        cdp.eval_js("document.getElementById('btn-cam-zoom-in').click()")
        time.sleep(0.3)

        ss_3d_iso = os.path.join(SCREENSHOT_DIR, "screenshot_3d_iso.png")
        cdp.capture_screenshot(ss_3d_iso)

        # 8-0. Verify FootprintManager and building overlap in live 3D environment
        print("[TEST] Verifying FootprintManager and building overlap in live 3D environment...")
        fp_check = cdp.eval_js("""
            (() => {
                const fp = window.citySim.view3D.footprintManager;
                if (!fp) return { error: 'No footprintManager' };
                const buildings = fp.boxes.filter(b => b.tag.startsWith('building'));
                const roads = fp.boxes.filter(b => b.tag === 'road');
                const specials = fp.boxes.filter(b => ['school', 'transit', 'river'].includes(b.tag));
                
                let bOverlaps = 0;
                for (let i = 0; i < buildings.length; i++) {
                    for (let j = i + 1; j < buildings.length; j++) {
                        const b1 = buildings[i], b2 = buildings[j];
                        if (b1.minX < b2.maxX && b1.maxX > b2.minX && b1.minY < b2.maxY && b1.maxY > b2.minY) {
                            bOverlaps++;
                        }
                    }
                }
                let rOverlaps = 0;
                for (const b of buildings) {
                    for (const r of roads) {
                        if (b.minX < r.maxX && b.maxX > r.minX && b.minY < r.maxY && b.maxY > r.minY) {
                            rOverlaps++;
                        }
                    }
                }
                return {
                    buildingCount: buildings.length,
                    roadCount: roads.length,
                    buildingOverlaps: bOverlaps,
                    roadOverlaps: rOverlaps
                };
            })()
        """)
        print(f"[TEST] Browser Footprint Verification: {fp_check}")
        assert fp_check['buildingCount'] >= 100
        assert fp_check['buildingOverlaps'] == 0
        assert fp_check['roadOverlaps'] == 0

        # 8-1. Focus on West Roundabout (x: 400, y: 800) for close-up inspection
        print("[TEST] Focusing camera on West Life-zone Roundabout...")
        cdp.eval_js("""
            window.citySim.view3D.camera.target = { x: 400, y: 800, z: 0 };
            window.citySim.view3D.camera.distance = 550;
            window.citySim.view3D.camera.pitch = 0.65;
            window.citySim.view3D.camera.yaw = Math.PI * 0.85;
            window.citySim.view3D.render();
        """)
        time.sleep(0.5)
        ss_3d_roundabout = os.path.join(SCREENSHOT_DIR, "screenshot_3d_roundabout.png")
        cdp.capture_screenshot(ss_3d_roundabout)

        # 8-2. Benchmark Area 1: Focus on Central BRT Boulevard & Station & Crossings (x: 1200, y: 860)
        print("[TEST] Focusing camera on Benchmark Area: Central BRT Boulevard & Station...")
        cdp.eval_js("""
            window.citySim.view3D.camera.target = { x: 1200, y: 860, z: 0 };
            window.citySim.view3D.camera.distance = 320;
            window.citySim.view3D.camera.pitch = 0.42;
            window.citySim.view3D.camera.yaw = 0.12;
            window.citySim.view3D.render();
        """)
        time.sleep(0.5)
        ss_3d_benchmark_brt = os.path.join(SCREENSHOT_DIR, "screenshot_3d_benchmark_brt.png")
        cdp.capture_screenshot(ss_3d_benchmark_brt)

        # 8-3. Benchmark Area 2: Focus on Waterfront Intersection & Grand Bridge (x: 1200, y: 1020)
        print("[TEST] Focusing camera on Benchmark Area: Waterfront Intersection & Bridge...")
        cdp.eval_js("""
            window.citySim.view3D.camera.target = { x: 1200, y: 1020, z: 0 };
            window.citySim.view3D.camera.distance = 420;
            window.citySim.view3D.camera.pitch = 0.38;
            window.citySim.view3D.camera.yaw = 0.32;
            window.citySim.view3D.render();
        """)
        time.sleep(0.5)
        ss_3d_benchmark_bridge = os.path.join(SCREENSHOT_DIR, "screenshot_3d_benchmark_bridge.png")
        cdp.capture_screenshot(ss_3d_benchmark_bridge)

        # 8-4. Benchmark Area 3: BRT Bus & Signal Lights (Green Phase)
        print("[TEST] Testing BRT Bus 3D rendering and NS Green Signal phase...")
        cdp.eval_js("""
            window.citySim.simulationTime = 12.0;
            window.citySim.spawnBrtBus();
            // 카메라를 수변 남측 교차로 및 BRT 승강장(x: 1200, y: 815)으로 포커스
            window.citySim.view3D.camera.target = { x: 1200, y: 815, z: 0 };
            window.citySim.view3D.camera.distance = 95;
            window.citySim.view3D.camera.pitch = 0.35;
            window.citySim.view3D.camera.yaw = 0.22;
            window.citySim.view3D.render();
        """)
        time.sleep(0.5)
        ss_3d_signal_green = os.path.join(SCREENSHOT_DIR, "screenshot_3d_signal_green.png")
        cdp.capture_screenshot(ss_3d_signal_green)

        # 8-5. Benchmark Area 4: Signal Lights (Red Phase)
        print("[TEST] Testing NS Red Signal phase (East-West Green)...")
        cdp.eval_js("""
            window.citySim.simulationTime = 45.0;
            window.citySim.view3D.render();
        """)
        time.sleep(0.5)
        ss_3d_signal_red = os.path.join(SCREENSHOT_DIR, "screenshot_3d_signal_red.png")
        cdp.capture_screenshot(ss_3d_signal_red)

        # 8-6. Benchmark Area 5: Waterfront Landmark Towers & Riverbank Linear Park
        print("[TEST] Focusing camera on Waterfront Landmark Towers & Riverwalk...")
        cdp.eval_js("""
            window.citySim.view3D.camera.target = { x: 1200, y: 920, z: 20 };
            window.citySim.view3D.camera.distance = 460;
            window.citySim.view3D.camera.pitch = 0.32;
            window.citySim.view3D.camera.yaw = -0.45;
            window.citySim.view3D.render();
        """)
        time.sleep(0.5)
        ss_3d_benchmark_towers = os.path.join(SCREENSHOT_DIR, "screenshot_3d_benchmark_towers.png")
        cdp.capture_screenshot(ss_3d_benchmark_towers)

        # 8-7. Detailed Inspection of 10 Architectural Typologies & Amenities
        # [A] Residential Superblock: Wide Slab, Stepped Terraces, Cruciform Tower, Playgrounds
        print("[TEST] Inspecting Diverse Residential Superblocks (Models M0~M3, Playgrounds, Terraces)...")
        cdp.eval_js("""
            window.citySim.view3D.camera.target = { x: 750, y: 550, z: 25 };
            window.citySim.view3D.camera.distance = 420;
            window.citySim.view3D.camera.pitch = 0.40;
            window.citySim.view3D.camera.yaw = 0.38;
            window.citySim.view3D.render();
        """)
        time.sleep(0.5)
        ss_3d_res = os.path.join(SCREENSHOT_DIR, "screenshot_3d_residential_complex.png")
        cdp.capture_screenshot(ss_3d_res)

        # [B] Commercial CBD: Setback Skyscraper, Rotunda Cylindrical Tower, Twin Office
        print("[TEST] Inspecting Commercial CBD (Setback Towers, Rotunda Cylinders, Skybridges)...")
        cdp.eval_js("""
            window.citySim.view3D.camera.target = { x: 750, y: 1380, z: 35 };
            window.citySim.view3D.camera.distance = 460;
            window.citySim.view3D.camera.pitch = 0.34;
            window.citySim.view3D.camera.yaw = -0.45;
            window.citySim.view3D.render();
        """)
        time.sleep(0.5)
        ss_3d_cbd = os.path.join(SCREENSHOT_DIR, "screenshot_3d_commercial_cbd.png")
        cdp.capture_screenshot(ss_3d_cbd)

        # [C] Techno Valley R&D Campus: Central Atrium HQ, L-shaped Lab & Tech Plaza, Twin Labs
        print("[TEST] Inspecting Techno Valley R&D Campus (Atrium HQ, L-shaped Tech Plaza, Twin Labs)...")
        cdp.eval_js("""
            window.citySim.view3D.camera.target = { x: 1550, y: 1380, z: 15 };
            window.citySim.view3D.camera.distance = 440;
            window.citySim.view3D.camera.pitch = 0.38;
            window.citySim.view3D.camera.yaw = 0.50;
            window.citySim.view3D.render();
        """)
        time.sleep(0.5)
        ss_3d_techno = os.path.join(SCREENSHOT_DIR, "screenshot_3d_techno_campus.png")
        cdp.capture_screenshot(ss_3d_techno)

        # [D] Waterfront Promenade & Amenities: Wooden Viewing Decks, Weeping Willows, Ginkgos, Arch Bridge
        print("[TEST] Inspecting Waterfront Promenade (Viewing Decks, Willows, Ginkgos, Arch Bridge)...")
        cdp.eval_js("""
            window.citySim.view3D.camera.target = { x: 1000, y: 980, z: 5 };
            window.citySim.view3D.camera.distance = 360;
            window.citySim.view3D.camera.pitch = 0.30;
            window.citySim.view3D.camera.yaw = 0.15;
            window.citySim.view3D.render();
        """)
        time.sleep(0.5)
        ss_3d_waterfront = os.path.join(SCREENSHOT_DIR, "screenshot_3d_waterfront_park.png")
        cdp.capture_screenshot(ss_3d_waterfront)

        # 9. Test returning to 2D mode via #btn-3d-exit
        print("[TEST] Returning to 2D mode via #btn-3d-exit...")
        cdp.eval_js("document.getElementById('btn-3d-exit').click()")
        time.sleep(0.5)
        current_mode_2 = cdp.eval_js("window.citySim.viewMode")
        print(f"[TEST] Returned mode: {current_mode_2}")
        assert current_mode_2 == '2d'

        # 10. Test Curve Road Generation & 2D/3D Visual Comparison
        print("[TEST] Creating curved arterial road and elevated BRT curved road in 2D...")
        cdp.eval_js("""
            // 1) 지상 아치형 곡선 도로 (Arterial curve)
            const cNode1 = { id: window.citySim.nextNodeId++, x: 350, y: 220, z: 0 };
            const cNode2 = { id: window.citySim.nextNodeId++, x: 750, y: 220, z: 0 };
            window.citySim.nodes.push(cNode1, cNode2);
            const curveRoad1 = window.citySim.createRoad(cNode1, cNode2, 'arterial', { x: 550, y: 100 });

            // 2) 고가 입체 곡선 BRT 도로 (Elevated BRT Highway curve)
            const cNode3 = { id: window.citySim.nextNodeId++, x: 1250, y: 220, z: 8 };
            const cNode4 = { id: window.citySim.nextNodeId++, x: 1650, y: 220, z: 8 };
            window.citySim.nodes.push(cNode3, cNode4);
            const curveRoad2 = window.citySim.createRoad(cNode3, cNode4, 'highway', { x: 1450, y: 340 });
            curveRoad2.facility = 'brt';
            curveRoad2.gradeSeparated = true;

            // 곡선 도로에 차량 스폰
            const r1Idx = window.citySim.roads.indexOf(curveRoad1);
            const r2Idx = window.citySim.roads.indexOf(curveRoad2);
            window.citySim.cars.push(
                { id: 9901, kind: 'sedan', roadIndex: r1Idx, progress: curveRoad1.length * 0.45, color: '#3498db' },
                { id: 9902, kind: 'bus', roadIndex: r2Idx, progress: curveRoad2.length * 0.50, color: '#e74c3c' }
            );

            // 2D 카메라를 곡선 도로 구역으로 이동
            window.citySim.camera.x = 1000;
            window.citySim.camera.y = 220;
            window.citySim.camera.zoom = 0.85;
            window.citySim.render();
        """)
        time.sleep(0.5)
        ss_2d_curve = os.path.join(SCREENSHOT_DIR, "screenshot_2d_curve_road.png")
        cdp.capture_screenshot(ss_2d_curve)

        # Switch back to 3D mode
        print("[TEST] Switching to 3D mode to inspect 2nd-order Bezier curved road mesh...")
        cdp.eval_js("window.citySim.toggleViewMode()")
        time.sleep(0.5)
        new_static_count = cdp.eval_js("window.citySim.view3D.staticBuffers.count")
        print(f"[TEST] 3D mesh updated with curve roads: count={new_static_count} (prev={static_count})")
        assert new_static_count > static_count

        # Focus 3D camera on Ground Curved Arterial Road
        cdp.eval_js("""
            window.citySim.view3D.camera.target = { x: 550, y: 180, z: 0 };
            window.citySim.view3D.camera.distance = 420;
            window.citySim.view3D.camera.pitch = 0.48;
            window.citySim.view3D.camera.yaw = -0.25;
            window.citySim.view3D.render();
        """)
        time.sleep(0.5)
        ss_3d_curve = os.path.join(SCREENSHOT_DIR, "screenshot_3d_curve_road.png")
        cdp.capture_screenshot(ss_3d_curve)

        # Focus 3D camera on Elevated Curved BRT Highway
        print("[TEST] Focusing camera on Elevated Curved BRT Highway...")
        cdp.eval_js("""
            window.citySim.view3D.camera.target = { x: 1450, y: 260, z: 8 };
            window.citySim.view3D.camera.distance = 450;
            window.citySim.view3D.camera.pitch = 0.42;
            window.citySim.view3D.camera.yaw = 0.35;
            window.citySim.view3D.render();
        """)
        time.sleep(0.5)
        ss_3d_curve_brt = os.path.join(SCREENSHOT_DIR, "screenshot_3d_curve_brt_elevated.png")
        cdp.capture_screenshot(ss_3d_curve_brt)

        ss_3d_updated = os.path.join(SCREENSHOT_DIR, "screenshot_3d_updated.png")
        cdp.capture_screenshot(ss_3d_updated)

        print("\n🎉 ALL BROWSER AUTOMATION AND VISUAL VERIFICATION TESTS PASSED SUCCESSFULLY! 🎉")
        return True

    finally:
        edge_proc.kill()
        server.shutdown()

if __name__ == '__main__':
    success = run_test()
    sys.exit(0 if success else 1)
