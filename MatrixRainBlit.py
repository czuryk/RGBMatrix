import displayio
import bitmaptools
import random

MAX_DROPS = 45

class MatrixRainBlit:
    def __init__(self, width, height, idx_head, idx_body, idx_tail):
        self.width = width
        self.height = height
        self.drops = [] 
        
        self.w_stamp = 4
        self.h_stamp = 16
        self.stamp = displayio.Bitmap(self.w_stamp, self.h_stamp, 4) 
        
        for y in range(16):
            if y < 6: color = idx_tail
            elif y < 12: color = idx_body
            else: color = idx_head
            for x in range(4): self.stamp[x, y] = color
        
    def spawn(self, count=1):
        if len(self.drops) >= MAX_DROPS: return
        w = self.width
        for _ in range(count):
            self.drops.append([random.randrange(0, w - 3, 4), 0.0, random.uniform(3.0, 6.0)]) 

    def spawn_column_drop(self, x, speed):
        drop = [x, 0.0, speed] 
        self.drops.append(drop)
        return drop

    def update(self, dest_bitmap):
        dest_bitmap.fill(0) 
        h_screen = self.height 
        stamp = self.stamp
        h_stamp = self.h_stamp
        active_drops = []
        blit = bitmaptools.blit 
        
        for drop in self.drops:
            drop[1] += drop[2] 
            y_curr = int(drop[1]) 
            if y_curr - h_stamp >= h_screen: continue
            active_drops.append(drop)
            
            x = drop[0]
            dest_y = y_curr - h_stamp
            
            if dest_y >= 0:
                 try:
                    blit(dest_bitmap, stamp, x, dest_y)
                 except ValueError: pass
            else:
                src_y = -dest_y
                if src_y < h_stamp:
                    try:
                        blit(dest_bitmap, stamp, x, 0, x1=0, y1=src_y, x2=4, y2=h_stamp)
                    except ValueError: pass
        self.drops = active_drops