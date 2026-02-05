import time
import board
import displayio
import framebufferio
import rgbmatrix
import terminalio
import wifi
import socketpool
import os
import rtc
import random
import gc
import adafruit_ntp
import bitmaptools
import adafruit_imageload
from adafruit_display_text import bitmap_label
from MatrixRainBlit import MatrixRainBlit

print("System Start: Matrix Clock Resurrection v1.0")

# --- USER SETTINGS ---
TZ_OFFSET = 1
SYNC_INTERVAL = 3600
BMP_ROOT_DIR = "/BMP"
NTP_SERVERS = ["time.google.com", "pool.ntp.org"]

# Animation Settings
MAX_DROPS = 45
TEXT_TOP_Y = 20           

# SCHEME GREEN
# Colors (R, G, B)
M_HEAD_DAY = 0x00BB00  
M_BODY_DAY = 0x006600  
M_TAIL_DAY = 0x002200  
M_TEXT_DAY = 0x00FF00  

M_HEAD_NIGHT = 0x006600
M_BODY_NIGHT = 0x004400
M_TAIL_NIGHT = 0x002200 
M_TEXT_NIGHT = 0x003300

# SCHEME PURPLE
# Colors (R, G, B)
# M_HEAD_DAY = 0x7134EB
# M_BODY_DAY = 0x482196
# M_TAIL_DAY = 0x200f42
# M_TEXT_DAY = 0x7634FA

# M_HEAD_NIGHT = 0x481162
# M_BODY_NIGHT = 0x271152
# M_TAIL_NIGHT = 0x271152
# M_TEXT_NIGHT = 0x271152


displayio.release_displays()

# --- MATRIX INITIALIZATION ---
addr_pins = [board.GP10, board.GP16, board.GP18, board.GP20, board.GP22]
rgb_pins = [board.GP2, board.GP3, board.GP4, board.GP5, board.GP8, board.GP9]

try:
    matrix = rgbmatrix.RGBMatrix(
        width=128, height=64, bit_depth=3,
        rgb_pins=rgb_pins, addr_pins=addr_pins,
        clock_pin=board.GP11, latch_pin=board.GP12, output_enable_pin=board.GP13,
        doublebuffer=True
    )
    display = framebufferio.FramebufferDisplay(matrix, auto_refresh=False)
except Exception as e:
    print("Matrix Init Error:", e)
    raise

# --- HELPER: SHUFFLE ---
def fisher_yates_shuffle(seq):
    for i in range(len(seq) - 1, 0, -1):
        j = random.randint(0, i)
        seq[i], seq[j] = seq[j], seq[i]

# --- TIME SYNCHRONIZATION ---
def sync_time():
    print("Connecting to Wi-Fi...")
    try:
        ssid = os.getenv("WIFI_SSID")
        password = os.getenv("WIFI_PASSWORD")
        
        if not wifi.radio.connected:
            wifi.radio.connect(ssid, password)
        
        print(f"Connected to {ssid}! IP: {wifi.radio.ipv4_address}")
        
        pool = socketpool.SocketPool(wifi.radio)
        
        for server in NTP_SERVERS:
            print(f"Trying NTP server: {server}...")
            try:
                ntp = adafruit_ntp.NTP(pool, server=server, tz_offset=os.getenv("TZ_OFFSET"))
                rtc.RTC().datetime = ntp.datetime
                print("Time synced successfully!")
                return True 
            except Exception as ntp_err:
                print(f"Server {server} failed: {ntp_err}")
                continue
                
    except Exception as e:
        print(f"General Connection Error: {e}")
    
    return False

def get_directories(path):
    folders = []
    try:
        for item in os.listdir(path):
            stats = os.stat(path + "/" + item)
            if stats[0] & 0x4000:
                folders.append(item)
    except OSError:
        print(f"Directory {path} not found.")
    return sorted(folders)

def get_bmp_files(path):
    bmp_files = []
    try:
        for item in os.listdir(path):
            if item.lower().endswith(".bmp") and not item.startswith("._"):
                bmp_files.append(item)
    except OSError:
        pass
    return sorted(bmp_files)

# --- MAIN CLOCK SCENE ---
def scene_matrix_clock(duration=30, is_night=False):
    if is_night:
        c_head, c_body, c_tail, c_text = M_HEAD_NIGHT, M_BODY_NIGHT, M_TAIL_NIGHT, M_TEXT_NIGHT
    else:
        c_head, c_body, c_tail, c_text = M_HEAD_DAY, M_BODY_DAY, M_TAIL_DAY, M_TEXT_DAY

    group = displayio.Group()
    
    font = terminalio.FONT
    lbl_time = bitmap_label.Label(font, text="00:00", color=c_text, scale=4)
    lbl_time.anchor_point = (0, 0.5) 
    lbl_time.x = 5 
    lbl_time.y = 32
    group.append(lbl_time)
    
    mask_bmp = displayio.Bitmap(128, 64, 2)
    mask_pal = displayio.Palette(2)
    mask_pal[0] = 0x00000000 
    mask_pal[1] = 0x000000   
    mask_pal.make_transparent(0)
    mask_grid = displayio.TileGrid(mask_bmp, pixel_shader=mask_pal)
    group.append(mask_grid)

    rain_bmp = displayio.Bitmap(128, 64, 4)
    rain_pal = displayio.Palette(4)
    rain_pal[0] = 0x000000 
    rain_pal[1] = c_tail
    rain_pal[2] = c_body
    rain_pal[3] = c_head
    rain_pal.make_transparent(0)
    rain_grid = displayio.TileGrid(rain_bmp, pixel_shader=rain_pal)
    group.append(rain_grid)
    
    display.root_group = group
    rain = MatrixRainBlit(128, 64, 3, 2, 1)
    
    start_time = time.monotonic()
    anim_state = 0 
    active_interactions = []
    pending_columns = []
    last_min = time.localtime().tm_min
    str_current = ""
    str_next = ""
    frame_timer = 0
    
    while (time.monotonic() - start_time < duration) or (anim_state != 0):
        now = time.localtime()
        separator = ":" if (time.time() % 2) < 1.0 or anim_state != 0 else " "
        
        # --- STATE MACHINE ---
        if anim_state == 0: 
            str_current = f"{now.tm_hour:02d}{separator}{now.tm_min:02d}"
            lbl_time.text = str_current
            
            if now.tm_min != last_min:
                anim_state = 1
                last_min = now.tm_min
                old_m = now.tm_min - 1
                old_h = now.tm_hour
                if old_m < 0:
                    old_m = 59
                    old_h -= 1
                    if old_h < 0: old_h = 23
                str_current = f"{old_h:02d}:{old_m:02d}"
                str_next = f"{now.tm_hour:02d}:{now.tm_min:02d}"
                lbl_time.text = str_current

        elif anim_state == 1: 
            gc.collect() 
            src_bmp = lbl_time.bitmap
            active_cols = set()
            for bx in range(src_bmp.width):
                for by in range(src_bmp.height):
                    if src_bmp[bx, by] != 0:
                        screen_x = lbl_time.x + (bx * 4)
                        grid_x = (screen_x // 4) * 4
                        if 0 <= grid_x < 128:
                            active_cols.add(grid_x)
                        break
            
            pending_columns = list(active_cols)
            fisher_yates_shuffle(pending_columns)
            active_interactions = []
            frame_timer = 0
            anim_state = 2
            
        elif anim_state == 2:
            frame_timer += 1
            rain_chance = frame_timer / 70.0 
            if random.random() < rain_chance: rain.spawn(1)

            interval = max(1, 40 // (len(pending_columns) + 1))
            if pending_columns and frame_timer % interval == 0:
                col_x = pending_columns.pop()
                spd = random.uniform(4.0, 6.0) 
                drop_ref = rain.spawn_column_drop(col_x, spd)
                active_interactions.append({'drop': drop_ref, 'col_x': col_x, 'action': 'hide', 'done': False})

            for interaction in active_interactions:
                if interaction['done']: continue
                d = interaction['drop']
                if d[1] >= TEXT_TOP_Y:
                    bitmaptools.fill_region(mask_bmp, interaction['col_x'], 0, interaction['col_x']+6, 64, 1)
                    interaction['done'] = True
            
            if not pending_columns and all(i['done'] for i in active_interactions):
                if frame_timer > 60:
                    anim_state = 3
                    frame_timer = 0

        elif anim_state == 3:
            if frame_timer == 0:
                mask_bmp.fill(1)          
                lbl_time.text = str_next  
                gc.collect()              

            if random.random() < 0.8: rain.spawn(1)
            frame_timer += 1
            
            if frame_timer > 30: 
                anim_state = 4
                src_bmp = lbl_time.bitmap
                active_cols = set()
                for bx in range(src_bmp.width):
                    for by in range(src_bmp.height):
                        if src_bmp[bx, by] != 0:
                            screen_x = lbl_time.x + (bx * 4)
                            grid_x = (screen_x // 4) * 4
                            if 0 <= grid_x < 128:
                                active_cols.add(grid_x)
                            break
                pending_columns = list(active_cols)
                fisher_yates_shuffle(pending_columns)
                active_interactions = []
                frame_timer = 0 

        elif anim_state == 4:
            if random.random() < 0.5: rain.spawn(1)
            frame_timer += 1
            interval = max(1, 50 // (len(pending_columns) + 1))
            
            if pending_columns and frame_timer % interval == 0:
                col_x = pending_columns.pop()
                spd = random.uniform(3.5, 5.0)
                drop_ref = rain.spawn_column_drop(col_x, spd)
                active_interactions.append({'drop': drop_ref, 'col_x': col_x, 'action': 'show', 'done': False})

            for interaction in active_interactions:
                if interaction['done']: continue
                d = interaction['drop']
                if d[1] >= TEXT_TOP_Y + 8: 
                    bitmaptools.fill_region(mask_bmp, interaction['col_x'], 0, interaction['col_x']+6, 64, 0)
                    interaction['done'] = True
            
            if not pending_columns and all(i['done'] for i in active_interactions):
                 if frame_timer > 100:
                    anim_state = 5

        elif anim_state == 5:
            if len(rain.drops) == 0:
                anim_state = 0
                mask_bmp.fill(0) 
                gc.collect()

        rain.update(rain_bmp)
        display.refresh(minimum_frames_per_second=0)

def scene_images(duration=10):
    gc.collect()

    folders = get_directories(BMP_ROOT_DIR)
    
    if not folders:
        print("No folders found in /BMP")
        return

    chosen_folder = random.choice(folders)
    full_path = BMP_ROOT_DIR + "/" + chosen_folder
    print(f"Scene: Animation from {full_path}")
    
    bmp_files = get_bmp_files(full_path)
    
    if not bmp_files:
        print(f"No BMP files in {chosen_folder}")
        return

    animation_frames = []
    
    try:
        for f in bmp_files:
            file_path = full_path + "/" + f
            bitmap, palette = adafruit_imageload.load(file_path, bitmap=displayio.Bitmap, palette=displayio.Palette)
            animation_frames.append((bitmap, palette))
    except Exception as e:
        print(f"Error loading frames: {e}")
        pass
    
    if not animation_frames:
        return

    group = displayio.Group()
    display.root_group = group

    img_idx = 0
    current_bitmap, current_palette = animation_frames[0]
    tilegrid = displayio.TileGrid(current_bitmap, pixel_shader=current_palette)
    group.append(tilegrid)
    display.refresh(minimum_frames_per_second=0)

    start_time = time.monotonic()
    last_switch = 0
    frame_duration = 0.1  # Animation Speed
    
    while time.monotonic() - start_time < duration:
        now = time.monotonic()
        
        if now - last_switch > frame_duration:
            img_idx = (img_idx + 1) % len(animation_frames)
           
            if len(group) > 0:
                group.pop()
            
            next_bitmap, next_palette = animation_frames[img_idx]
            new_tilegrid = displayio.TileGrid(next_bitmap, pixel_shader=next_palette)
            group.append(new_tilegrid)
            
            last_switch = now
            display.refresh(minimum_frames_per_second=0)
            
        time.sleep(0.01)

    # Free memory
    del animation_frames
    del group
    gc.collect()
    print(f"Memory free: {gc.mem_free()}")


# --- MAIN LOOP ---
print("Starting Loop...")
gc.collect()
sync_time()
last_sync = time.time()

while True:
    if time.time() - last_sync > SYNC_INTERVAL:
        if sync_time(): last_sync = time.time()
            
    h = time.localtime().tm_hour
    is_night = (h >= 0 and h < 7)

    is_night = False # Override night for demo

    if is_night:
        scene_matrix_clock(duration=59, is_night=is_night)
        gc.collect()
    else:
        scene_matrix_clock(duration=59, is_night=is_night) # Show tide with animation for 1 minutes and repeat
        gc.collect()
        scene_images(10) # Show images animation for 10 seconds
        