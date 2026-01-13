import pygame
from random import randint

pygame.init()
width,height=400,600
#chiều rộng và chiều cao cửa sổ
screen = pygame.display.set_mode((width, height))
# window size
pygame.display.set_caption("fly bird")

running = True
green = (0, 200, 0)
blue=(0,0,255)
red=(255,0,0)

clock = pygame.time.Clock()


tube_width=50
#chiều dài ống là 50
tube1_x=0
tube2_x=200
tube3_x=400
#tọa độ của ống
tube1_height=randint(100,400)
tube2_height=randint(100,400)
tube3_height=randint(100,400)

#tọa độ chim ở hàng ngang xuất hiện
bird_x=50
#tọa đọ chiều cao của chim
bird_y=300
#đọ dài và ngang của chim
bird_weight=35
bird_height=25
#chim rơi xuống
bird_drop_speed=0
gravity=0.5


#chiều cao của ống
tube_speed=3
#tốc đọ di chuyển của ống
tube_gap=150
#khoảng cách giữa 2 ống
while running:
    clock.tick(60)
    screen.fill(green)
#ống trên
    pygame.draw.rect(screen,blue,(tube1_x,0,tube_width,tube1_height))
    pygame.draw.rect(screen,blue,(tube2_x,0,tube_width,tube2_height))
    pygame.draw.rect(screen,blue,(tube3_x,0,tube_width,tube3_height))


    #ống dưới
    pygame.draw.rect(screen,blue,(tube1_x,tube1_height+tube_gap,tube_width,height-tube1_height-tube_gap))
    pygame.draw.rect(screen,blue,(tube2_x,tube2_height+tube_gap,tube_width,height-tube2_height-tube_gap))
    pygame.draw.rect(screen,blue,(tube3_x,tube3_height+tube_gap,tube_width,height-tube3_height-tube_gap))
#di chuyển
    tube1_x=tube1_x-tube_speed
    tube2_x=tube2_x-tube_speed
    tube3_x=tube3_x-tube_speed


    #viet chim
    pygame.draw.rect(screen,red,(bird_x,bird_y,bird_height,bird_weight))
    #chim roi
    bird_y=bird_y+bird_drop_speed
    bird_drop_speed=bird_drop_speed+gravity

#tạo ống mới

    if tube1_x<-tube_width:
        tube1_x=550
        tube1_height=randint(100,400)
        
    if tube2_x<-tube_width:
        tube2_x=550
        tube2_height=randint(100,400)
    if tube3_x<-tube_width:
        tube3_x=550
        tube3_height=randint(100,400)
    for event in pygame.event.get():
        # hàm event để sử dụng phím chuột và bàn phím
        if event.type == pygame.QUIT:
            running = False
        if event.type ==pygame.KEYDOWN:
            if event.key==pygame.K_SPACE:
                bird_drop_speed=0
                bird_drop_speed=bird_drop_speed-10

    pygame.display.flip()

pygame.quit()
