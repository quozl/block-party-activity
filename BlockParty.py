#  restit 

import pygtk
pygtk.require('2.0')
import gtk
import operator
import time
import string
import gobject
import math
import pickle
import getopt
import sys
import random
import copy
import pango
import socket
import os

#class Tetromino

bwpx,bhpx,score,bw,bh,glass,cnt=0,0,0,10,20,[],0
xshift, yshift = 0, 0
colors=['black', 'blue', 'green', 'cyan', 'red', 'magenta','YellowGreen', 'white']
figures=[[[0,0,0,0],
          [0,1,1,0],
          [0,1,1,0],
          [0,0,0,0]],
         [[0,0,0,0],
          [0,2,2,0],
          [2,2,0,0],
          [0,0,0,0]],
         [[0,0,0,0],
          [3,3,0,0],
          [0,3,3,0],
          [0,0,0,0]],
         [[0,0,0,0],
          [4,4,4,4],
          [0,0,0,0],
          [0,0,0,0]],
         [[0,0,0,0],
          [0,5,5,5],
          [0,5,0,0],
          [0,0,0,0]],
         [[0,0,0,0],
          [6,6,6,0],
          [0,6,0,0],
          [0,0,0,0]],
         [[0,0,0,0],
          [0,7,0,0],
          [0,7,7,7],
          [0,0,0,0]]]

left_key  = ['Left', 'KP_Left']
right_key  = ['Right', 'KP_Right']
drop_key  = ['space', 'KP_Down']
rotate_key = ['Up', 'KP_Up']
exit_key = ['Escape']
sound_toggle_key = ['s', 'S']
enter_key  = ['Return']

figure,px,py = None, 0, 0

next_figure = None
xnext, ynext = 0, 0

tickcnt = 0
cm = None
area = None
windows = None
linecount = 0
score = 0
level = 0
figure_score = 0
scorefont = None
color_back, color_glass, color_score = None, None, None

scorex, scorey = 20, 100

time_step, next_tick = 100, time.time()+100

complete_update, glass_update = False, False

IDLE, SELECT_LEVEL, PLAY, GAME_OVER = 0, 1, 2, 3

game_mode = IDLE

sound = False
soundon = True
cssock = None
csid = 544554

def draw_glass():
   global area, gc, window, glass, cm, cmap, bh, bw, px, py
   for i in range(bh):
      for j in range(bw):
         if glass[i][j] < 0:
            gc.set_foreground(colors[0])
            area.draw_rectangle(gc, True, xshift+j*bwpx, yshift+(bh-i-1)*bhpx, bwpx, bhpx)
            gc.set_foreground(colors[-glass[i][j]])
            area.draw_rectangle(gc, True, xshift+j*bwpx+bwpx/4, yshift+(bh-i-1)*bhpx+bhpx/4, bwpx/2, bhpx/2)
         else:   
            c=colors[glass[i][j]]
            if (i in range(py,py+4)) and (j in range(px,px+4)):
               if figure[i-py][j-px]!=0: c=colors[figure[i-py][j-px]]
            gc.set_foreground(c)
            area.draw_rectangle(gc, True, xshift+j*bwpx, yshift+(bh-i-1)*bhpx, bwpx, bhpx)

def quit_game():
#   sleep(500)
   sys.exit()

def key_action(key):
   global figure,px,py,tickcnt
   global glass_update
   global game_mode
   global soundon
   global level
   global next_tick, time_step
   if key in exit_key: quit_game()
   if key in sound_toggle_key: soundon = not soundon
   if game_mode == SELECT_LEVEL:
      if key in left_key:
         set_level(level-1)
         glass_update = True
      else:
          if key in right_key:
              set_level(level+1)
              glass_update = True
          else: # if key in enter_key:
              complete_update = True
              next_tick = time.time()+time_step
              game_mode = PLAY
      update_picture()
#      try: new_level = int(key)
#      except: new_level = -1
#      if new_level >= 0 and new_level <= 9: 
#         set_level(new_level)
#         game_mode = PLAY
      return
   if game_mode == IDLE:
      return
   if game_mode == GAME_OVER:
#      print 'Starting new game...'
      init_game()
      return 
   changed = False
   if key in left_key:
      px-=1 
      if not figure_fits(): px+=1
      else: changed=True
   if key in right_key:
      px+=1 
      if not figure_fits(): px-=1
      else: changed=True
   if key in drop_key:
      changed = drop_figure()
   if key in rotate_key:
      changed = rotate_figure_ccw(True)
   if changed:
      glass_update = True
      update_picture()

def tick():
   global figure, px, py, tickcnt, bh
   global figure_score
   global complete_update, glass_update
   global level, linecount
   global game_mode
   glass_update = True
   py-=1
   if figure_score > 0: figure_score -= 1
   if not figure_fits():
      py+=1
      put_figure()
      make_sound('heart.wav')
      new_figure()
      if not figure_fits():
         i = random.randint(0, 2)
         if i is 0: make_sound('ouch.wav')
         if i is 1: make_sound('wah.au'),
         if i is 2: make_sound('lost.wav')
         print 'GAME OVER: score ' + str(score)
         game_mode = GAME_OVER
         complete_update = True
         update_picture()
         return
#         quit_game()
#      window.queue_draw()
   chk_glass()
   new_level = int(linecount/5)
   if new_level > level: set_level(new_level)
   tickcnt += 1
   update_picture()

def new_figure():
   global figure, next_figure, px, py, bh
   global figure_score
   figure_score = bh + level
   figure = copy.deepcopy(figures[random.randint(0,len(figures)-1)])
   for i in range(random.randint(0, 3)): rotate_figure_ccw(False)
   tmp = figure
   figure = next_figure
   next_figure = tmp
   px=bw / 2 - 2 #+ random.randint(-3, 3) #-len(figure.split('\n')[0])/2
   py=bh - 3
   if figure is None: new_figure()

def rotate_figure_cw(check_fit):
   global figure
   oldfigure = copy.deepcopy(figure)
   for i in range(4):
      for j in range(4):
         figure[i][j]=oldfigure[j][3-i]
   if not check_fit or figure_fits(): return True
   else:
      figure=oldfigure
      return False

def rotate_figure_ccw(check_fit):
   global figure
   oldfigure = copy.deepcopy(figure)
   for i in range(4):
      for j in range(4):
         figure[i][j]=oldfigure[3-j][i]
   if not check_fit or figure_fits(): return True
   else:
      figure=oldfigure
      return False

def drop_figure():
   global figure, px, py
   oldy = py
   py-=1
   while figure_fits(): py -= 1
   py+=1
   return oldy!=py 

def figure_fits():
   global figure, px, py
   for i in range(4):
      for j in range(4):
         if figure[i][j] != 0:
           if i+py<0 or j+px<0 or j+px>=bw: return False
           if i+py<bh: 
             if glass[i+py][j+px] != 0: return False
   return True 

def put_figure():
   global glass, figure, px, py
   global score, figure_score
   score += figure_score
   for i in range(4):
      for j in range(4):
         if i+py<bh and figure[i][j] != 0: glass[i+py][j+px]=figure[i][j]

def chk_glass():
   global glass, score, linecount
   global next_tick, time_step
   clearlines = []
   for i in range(bh-1, -1, -1):
      j = 0
      while j<bw and glass[i][j]!=0: j+=1
      if j>=bw:
         clearlines.append(i)
         linecount+=1
         for j in range(bw):
            glass[i][j] = -glass[i][j]
   if len(clearlines)>0:         
      make_sound('boom.au')
      draw_glass()
      time.sleep(time_step)
      for i in clearlines:
         for j in range(bw): glass[i][j] = 0
      draw_glass()
      time.sleep(time_step)
      next_tick+=time_step*2
   for i in clearlines:
      tmp = glass[i]
      for ii in range(i, bh-1):
         glass[ii] = glass[ii+1]
      glass[bh-1] = tmp

def draw_background():
   global gc, xshift, yshift, bw, bh, bwpx, bhpx
   global color_back, color_glass
   gc.set_foreground(color_back)
   area.draw_rectangle(gc, True, 0, 0, window_w, window_h)
   gc.set_foreground(color_glass)
   area.draw_rectangle(gc, True, xshift-bwpx/2, yshift, bwpx*(bw+1), bhpx*bh+bhpx/2)

def expose_cb(widget, event):
   global complete_update
   complete_update = True
   update_picture() 
   return True

def update_picture():
   global complete_update, glass_update
#   print "e"
   if complete_update:
      draw_background()
      draw_score()
   if complete_update or glass_update:
      draw_glass()
      draw_next()
      if game_mode is GAME_OVER: draw_game_end_poster()
      if game_mode is SELECT_LEVEL: draw_select_level_poster()
   complete_update = False
   glass_update = False

def keypress_cb(widget, event):
#   print gtk.gdk.keyval_name(event.keyval)
   key_action(gtk.gdk.keyval_name(event.keyval))
   return True

def keyrelease_cb(widget, event):
   global window
   return True

def timer():
    global game_mode
    global next_tick, time_step
    while game_mode == PLAY and time.time() >= next_tick:
        next_tick += time_step
        tick()  
#       print time.time()
#    window.queue_draw()
    if game_mode != PLAY:
        next_tick = time.time()+100
    return True

def draw_centered_string(string, x, y):
    global gc, window
    pl = window.create_pango_layout(string)
    pl.set_font_description(scorefont)
    width = pl.get_size()[0]/pango.SCALE
    area.draw_layout(gc, int(x - width / 2), int(y), pl)

def draw_game_end_poster():
    global gc, area, window
    global bw, bh, bwpx, bhpx, xshift, yshift
    gc.set_foreground(colors[0])
    area.draw_rectangle(gc, True, xshift, yshift+(bh/2-3)*bhpx, bw*bwpx, 6*bhpx)
    gc.set_foreground(color_score)
    draw_centered_string('GAME OVER', xshift+(bwpx*bw)/2, yshift+(bh/2-1)*bhpx)    
    draw_centered_string('Again? (x/o)', xshift+(bwpx*bw)/2, yshift+(bh/2+1)*bhpx)    

def draw_score():
    global gc, area
    global linecount, score, level, scorefont
    global scorex, scorey
    global color_score
    displaystr = 'Score: ' + str(score)
    displaystr += '\nLevel: ' + str(level)
    displaystr += '\nLines: ' + str(linecount)
    pl = window.create_pango_layout(displaystr)
    pl.set_font_description(scorefont)
    gc.set_foreground(color_score)
    area.draw_layout(gc, scorex, scorey, pl)

def set_level(new_level):    
    global level, next_tick, time_step
    level = new_level
    if level < 0: level = 0
    if level > 9: level = 9
    time_step = 0.1 + (9-level)*0.1
    next_tick = time.time()+time_step
    
def draw_select_level_poster():    
    global gc, area, window
    global level
    global bw, bh, bwpx, bhpx, xshift, yshift
    gc.set_foreground(colors[0])
    area.draw_rectangle(gc, True, xshift, yshift+(bh/2-3)*bhpx, bw*bwpx, 6*bhpx)
    gc.set_foreground(color_score)
    draw_centered_string('SELECT', xshift+(bwpx*bw)/2, yshift+(bh/2-2)*bhpx)    
    draw_centered_string('LEVEL: '+str(level), xshift+(bwpx*bw)/2, yshift+(bh/2)*bhpx)    
    draw_centered_string('enter to start', xshift+(bwpx*bw)/2, yshift+(bh/2+2)*bhpx)    

def clear_glass():
    global glass
    for i in range(bh):
       for j in range(bw):
          glass[i][j]=0

def init_game():
#    print 'Init Game'
    global game_mode
    global linecount, score, level
    global complete_update, glass_update
    clear_glass()
    complete_update = True
    glass_update = True
    linecount = 0
    score = 0
    new_figure()
    set_level(5)
    game_mode = SELECT_LEVEL
    update_picture()
#    set_level(0)
#    game_mode = PLAY

def csconnect():
    global cssock, sound, csid
    if cssock!=None:
        cssock.close()
    cssock = socket.socket()
    sound = False
    if cssock: 
        try:
            cssock.connect(('127.0.0.1', 6783))
#            print "Connected to csound server"
            sound = True   
            msg = "csound.SetChannel('sfplay.%d.on', 1)\n" % csid
            cssock.send(msg)     
        except:
            cssock.close()
            print "Sound server does not respond "    

def draw_next():
    global gc, area, window, next_figure
    global bw, bh, bwpx, bhpx, xshift, yshift
    gc.set_foreground(color_score)
    draw_centered_string('NEXT', xnext+bwpx*2.5, ynext)    
    gc.set_foreground(colors[0])
    area.draw_rectangle(gc, True, xnext, ynext+50, bwpx*5, bhpx*5)
    gc.set_foreground(color_score)
    for i in range(4):
        for j in range(4):
            if next_figure[i][j] is not 0:
                gc.set_foreground(colors[next_figure[i][j]])
	        area.draw_rectangle(gc, True, xnext+j*bwpx+bwpx/2, ynext+50+(3-i)*bhpx+bhpx/2, bwpx, bhpx)


def make_sound(filename):
    global cssock, sound, soundon, csid
    if sound and soundon:
        msg = "perf.InputMessage('i 108 0 3 \"%s\" %d 0.7 0.5 0')\n" % (os.path.abspath(filename), csid)
        cssock.send(msg)

def init():
    global glass, bwpx, bhpx, bw, bh, xshift, yshift, xnext, ynext
    global window, area, gc, glass, cm, cmap, scorefont
    global window_w, window_h
    global color_back, color_glass, color_score
    glass=[[0]*bw for i in range(bh)]
    window = gtk.Window(gtk.WINDOW_TOPLEVEL)
    window_w = window.get_screen().get_width()
    window_h = window.get_screen().get_height()
    if window_w > 1024: window_w=1024
    if window_h > 728: window_h=728
    window.set_title("Block Party")
    window.connect("destroy", lambda w: gtk.main_quit())
    window.set_size_request(window_w, window_h)
    window.connect("expose_event", expose_cb)
    window.connect("key_press_event", keypress_cb)
    window.connect("key_release_event", keyrelease_cb)
    window.show()
    area = window.window
#    area.set_cursor(invisible)
    gc = area.new_gc() 
    cm = gc.get_colormap()
    color_back = cm.alloc_color("white")
    color_glass = cm.alloc_color("grey")
    color_score = cm.alloc_color("grey26")
    bwpx=int(window_w/(bw+bw/2+2))
    bhpx=int(window_h/(bh+2))
    if bwpx < bhpx: bhpx = bwpx
    else: bwpx = bhpx
    xshift = int((window_w - (bw+1)*bwpx) / 2)
    yshift = int((window_h - (bh+1)*bhpx) / 2)
    xnext = xshift + (bw+3)*bwpx
    ynext = yshift
    for i in range(len(colors)):
      colors[i] = cm.alloc_color(colors[i])
    scorefont = pango.FontDescription('Sans')
    scorefont.set_size(window_w*16*pango.SCALE/1024)
    csconnect()
    gobject.timeout_add(20, timer)
    init_game()

def main():
    init()
    gtk.main()
    return 0

if __name__ == "__main__":
    main()

