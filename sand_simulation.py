import pygame
import random
import sys

# 初始化 Pygame
pygame.init()

# 常量定义
WINDOW_WIDTH = 600
WINDOW_HEIGHT = 1000
SAND_SIZE = 8  # Increased from 3 to 8 pixels
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
        self.height_threshold = 2
        self.square_size = 20
        self.connected_sand_timer = None
        self.sand_to_remove = None
        self.touch_timer = None  # Timer for when sand touches
        self.touch_delay = 20   # Delay in milliseconds before checking connection
    
    def find_connected_sand(self, start_x, start_y, visited):
        """Find all connected sand particles using iterative flood fill with 8-direction check"""
        if (start_x < 0 or start_x >= WINDOW_WIDTH//SAND_SIZE or
            start_y < 0 or start_y >= WINDOW_HEIGHT//SAND_SIZE or
            not self.grid[start_x][start_y] or
            (start_x, start_y) in visited):
            return set()
        
        connected = set()
        stack = [(start_x, start_y)]
        
        while stack:
            x, y = stack.pop()
            
            if (x, y) in visited:
                continue
                
            visited.add((x, y))
            connected.add((x, y))
            
            # Check all 8 directions (including diagonals)
            directions = [
                (0, 1), (0, -1), (1, 0), (-1, 0),  # orthogonal
                (1, 1), (1, -1), (-1, 1), (-1, -1)  # diagonal
            ]
            for dx, dy in directions:
                next_x, next_y = x + dx, y + dy
                if (next_x >= 0 and next_x < WINDOW_WIDTH//SAND_SIZE and
                    next_y >= 0 and next_y < WINDOW_HEIGHT//SAND_SIZE and
                    self.grid[next_x][next_y] and
                    (next_x, next_y) not in visited):
                    stack.append((next_x, next_y))
        
        return connected
    
    def check_and_remove_connected_sand(self):
        """Check for sand that touches both bounds and remove it if found"""
        current_time = pygame.time.get_ticks()
        
        # If we're already waiting to remove sand, check if time has elapsed
        if self.connected_sand_timer is not None:
            if current_time - self.connected_sand_timer >= 20:
                if self.sand_to_remove:
                    for x, y in self.sand_to_remove:
                        self.grid[x][y] = False
                    new_particles = []
                    remove_positions = {(x, y) for x, y in self.sand_to_remove}
                    for sand in self.sand_particles:
                        grid_x, grid_y = int(sand.x//SAND_SIZE), int(sand.y//SAND_SIZE)
                        if (grid_x, grid_y) not in remove_positions:
                            new_particles.append(sand)
                    self.sand_particles = new_particles
                self.connected_sand_timer = None
                self.sand_to_remove = None
            return

        # If touch timer is not set or hasn't elapsed, don't check for connections
        if self.touch_timer is None:
            self.touch_timer = current_time
            return
        elif current_time - self.touch_timer < self.touch_delay:
            return
        
        visited = set()
        all_connected = set()
        
        # Check each row for connected sand
        for y in range(WINDOW_HEIGHT // SAND_SIZE):
            if self.grid[0][y]:
                connected = self.find_connected_sand(0, y, visited)
                if any(x == (WINDOW_WIDTH//SAND_SIZE - 1) for x, _ in connected):
                    all_connected.update(connected)
            
            if self.grid[WINDOW_WIDTH//SAND_SIZE - 1][y]:
                connected = self.find_connected_sand(WINDOW_WIDTH//SAND_SIZE - 1, y, visited)
                if any(x == 0 for x, _ in connected):
                    all_connected.update(connected)
        
        if all_connected:
            self.connected_sand_timer = current_time
            self.sand_to_remove = all_connected
            self.touch_timer = None  # Reset touch timer after finding connection
    
    def add_sand_square(self, center_x):
        # Calculate the top-left corner of the square
        start_x = center_x - (self.square_size * SAND_SIZE) // 2
        
        # Add sand particles in a square pattern
        for row in range(self.square_size):
            for col in range(self.square_size):
                x = start_x + (col * SAND_SIZE)
                y = row * SAND_SIZE
                
                # Ensure the sand is within screen bounds
                if 0 <= x < WINDOW_WIDTH and 0 <= y < WINDOW_HEIGHT:
                    grid_x = int(x // SAND_SIZE)
                    grid_y = int(y // SAND_SIZE)
                    
                    if not self.grid[grid_x][grid_y]:
                        new_sand = SandGrain(x, y)
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
        any_movement = False
        
        for sand in self.sand_particles:
            initial_pos = (sand.x, sand.y)
            
            if sand.settled:
                x, y = int(sand.x // SAND_SIZE), int(sand.y // SAND_SIZE)
                slide_direction = self.check_slope(x, y)
                if slide_direction != 0 and random.random() < self.slide_chance:
                    self.grid[x][y] = False
                    sand.settled = False
                    new_x = (x + slide_direction) * SAND_SIZE
                    if 0 <= new_x < WINDOW_WIDTH and not self.grid[x + slide_direction][y]:
                        sand.x = new_x
                        any_movement = True
                continue
            
            new_x = int(sand.x // SAND_SIZE)
            new_y = int((sand.y + SAND_SIZE) // SAND_SIZE)
            
            if new_y >= WINDOW_HEIGHT//SAND_SIZE or self.grid[new_x][new_y]:
                current_y = int(sand.y // SAND_SIZE)
                slide_direction = self.check_slope(new_x, current_y)
                if slide_direction != 0:
                    test_x = new_x + slide_direction
                    if (0 <= test_x < WINDOW_WIDTH//SAND_SIZE and 
                        not self.grid[test_x][current_y]):
                        sand.x = test_x * SAND_SIZE
                        any_movement = True
                        continue
                
                sand.settled = True
                self.grid[new_x][current_y] = True
                sand.x = new_x * SAND_SIZE
                sand.y = current_y * SAND_SIZE
                continue
            
            if not self.grid[new_x][new_y]:
                sand.y += SAND_SIZE
                any_movement = True
            
            if (sand.x, sand.y) != initial_pos:
                any_movement = True
        
        # Only check for connected sand if there's no movement
        if not any_movement:
            self.check_and_remove_connected_sand()
        else:
            self.touch_timer = None  # Reset touch timer if there's movement
    
    def draw(self, surface):
        for sand in self.sand_particles:
            pygame.draw.rect(surface, sand.color, 
                           (int(sand.x), int(sand.y), SAND_SIZE, SAND_SIZE))

def main():
    simulation = SandSimulation()
    running = True
    mouse_pressed = False
    last_spawn_time = 0
    spawn_delay = 500  # Delay in milliseconds between square spawns

    while running:
        current_time = pygame.time.get_ticks()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pressed = True
            elif event.type == pygame.MOUSEBUTTONUP:
                mouse_pressed = False
        
        if mouse_pressed and current_time - last_spawn_time > spawn_delay:
            mouse_x, _ = pygame.mouse.get_pos()
            simulation.add_sand_square(mouse_x)
            last_spawn_time = current_time
        
        # Update sand positions
        simulation.update()
        
        # Draw
        screen.fill(BLACK)
        simulation.draw(screen)
        pygame.display.flip()
        
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main()