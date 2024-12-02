import pygame
import random
import sys

# 初始化 Pygame
pygame.init()

# 常量定义
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
SAND_SIZE = 3  # 增加沙粒大小
FPS = 60       # 调整帧率

# 颜色定义
BLACK = (0, 0, 0)
SAND_COLORS = [
    (194, 178, 128),  # 浅沙色
    (189, 174, 124),  # 沙色变体1
    (199, 183, 133),  # 沙色变体2
    (201, 186, 136),  # 沙色变体3
    (187, 171, 121),  # 沙色变体4
]

# 创建窗口
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption('Sand Simulation')
clock = pygame.time.Clock()

class SandGrain:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.color = random.choice(SAND_COLORS)
        self.settled = False
        self.sliding = False  # 是否正在滑动

class SandSimulation:
    def __init__(self):
        self.sand_particles = []
        self.grid = [[False for _ in range(WINDOW_HEIGHT // SAND_SIZE)] 
                    for _ in range(WINDOW_WIDTH // SAND_SIZE)]
        self.max_slope = 1
        self.slide_chance = 0.95
        self.height_threshold = 2  # 高度差阈值
    
    def add_sand(self, x):
        # 在顶部添加新的沙粒
        new_sand = SandGrain(x, 0)
        self.sand_particles.append(new_sand)
    
    def check_slope(self, x, y):
        # 检查左右两侧的高度差
        left_height = 0
        right_height = 0
        
        # 检查左侧高度差
        if x > 0:
            check_y = y
            while (check_y < (WINDOW_HEIGHT//SAND_SIZE) and 
                   not self.grid[x-1][check_y]):
                left_height += 1
                check_y += 1
                if left_height > self.height_threshold:
                    break
        
        # 检查右侧高度差
        if x < (WINDOW_WIDTH//SAND_SIZE)-1:
            check_y = y
            while (check_y < (WINDOW_HEIGHT//SAND_SIZE) and 
                   not self.grid[x+1][check_y]):
                right_height += 1
                check_y += 1
                if right_height > self.height_threshold:
                    break
        
        # 如果高度差超过阈值，决定滑落方向
        if left_height > self.height_threshold or right_height > self.height_threshold:
            # 优先向高度差更大的方向滑落
            if left_height > right_height:
                return -1 if x > 0 and not self.grid[x-1][y] else 0
            elif right_height > left_height:
                return 1 if x < (WINDOW_WIDTH//SAND_SIZE)-1 and not self.grid[x+1][y] else 0
            else:
                # 如果两边高度差相同，随机选择方向
                possible_dirs = []
                if x > 0 and not self.grid[x-1][y]:
                    possible_dirs.append(-1)
                if x < (WINDOW_WIDTH//SAND_SIZE)-1 and not self.grid[x+1][y]:
                    possible_dirs.append(1)
                return random.choice(possible_dirs) if possible_dirs else 0
        
        # 如果没有显著的高度差，检查普通的滑动条件
        left_empty = x > 0 and not self.grid[x-1][y]
        right_empty = x < (WINDOW_WIDTH//SAND_SIZE)-1 and not self.grid[x+1][y]
        
        if y < (WINDOW_HEIGHT//SAND_SIZE)-1:
            left_support = x > 0 and self.grid[x-1][y+1]
            center_support = self.grid[x][y+1]
            right_support = x < (WINDOW_WIDTH//SAND_SIZE)-1 and self.grid[x+1][y+1]
            
            if not center_support:
                if left_support and right_support:
                    return random.choice([-1, 1]) if random.random() < 0.5 else 0
                elif left_support and left_empty:
                    return 1
                elif right_support and right_empty:
                    return -1
                elif left_empty and right_empty:
                    return random.choice([-1, 1])
        return 0
    
    def update(self):
        for sand in self.sand_particles:
            if sand.settled:
                x, y = int(sand.x // SAND_SIZE), int(sand.y // SAND_SIZE)
                
                # 检查是否需要滑动
                slide_direction = self.check_slope(x, y)
                if slide_direction != 0 and random.random() < self.slide_chance:
                    self.grid[x][y] = False
                    sand.settled = False
                    new_x = (x + slide_direction) * SAND_SIZE
                    if 0 <= new_x < WINDOW_WIDTH and not self.grid[x + slide_direction][y]:
                        sand.x = new_x
                continue
            
            new_x = int(sand.x // SAND_SIZE)
            new_y = int((sand.y + SAND_SIZE) // SAND_SIZE)
            
            # 检查是否到达底部或遇到其他沙粒
            if new_y >= WINDOW_HEIGHT//SAND_SIZE or self.grid[new_x][new_y]:
                # 尝试滑向两边
                current_y = int(sand.y // SAND_SIZE)
                slide_direction = self.check_slope(new_x, current_y)
                if slide_direction != 0:
                    test_x = new_x + slide_direction
                    if (0 <= test_x < WINDOW_WIDTH//SAND_SIZE and 
                        not self.grid[test_x][current_y]):
                        sand.x = test_x * SAND_SIZE
                        continue
                
                # 如果无法移动，则停止
                sand.settled = True
                self.grid[new_x][current_y] = True
                sand.x = new_x * SAND_SIZE
                sand.y = current_y * SAND_SIZE
                continue
            
            # 正常下落
            if not self.grid[new_x][new_y]:
                sand.y += SAND_SIZE
                # 随机左右偏移
                if random.random() < 0.2:
                    offset = random.choice([-1, 1])
                    test_x = new_x + offset
                    if (0 <= test_x < WINDOW_WIDTH//SAND_SIZE and 
                        not self.grid[test_x][new_y]):
                        sand.x = test_x * SAND_SIZE
    
    def draw(self, surface):
        for sand in self.sand_particles:
            pygame.draw.rect(surface, sand.color, 
                           (int(sand.x), int(sand.y), SAND_SIZE, SAND_SIZE))

def main():
    simulation = SandSimulation()
    running = True
    mouse_pressed = False

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pressed = True
            elif event.type == pygame.MOUSEBUTTONUP:
                mouse_pressed = False
        
        if mouse_pressed:
            mouse_x, _ = pygame.mouse.get_pos()
            # 每帧添加沙粒
            for _ in range(3):  # 减少每帧添加的数量
                offset = random.randint(-2, 2) * SAND_SIZE
                x = (mouse_x + offset) // SAND_SIZE * SAND_SIZE
                if (0 <= x < WINDOW_WIDTH and 
                    not simulation.grid[int(x//SAND_SIZE)][0]):
                    simulation.add_sand(x)
        
        # 更新沙子位置
        simulation.update()
        
        # 绘制
        screen.fill(BLACK)
        simulation.draw(screen)
        pygame.display.flip()
        
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main()